import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ConvertoAI Enterprise Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client()

# --- LIVE SQL DATABASE UTILITIES ---

def get_product_details(product_key: str) -> dict:
    """Retrieves real-time stock, pricing, and sizing data from the live store.db file."""
    try:
        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        # Clean string inputs to prevent lookup mismatches
        clean_key = str(product_key).lower().strip()
        cursor.execute("SELECT name, price, stock, sizes FROM inventory WHERE id = ?", (clean_key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {"name": row[0], "price": float(row[1]), "stock": int(row[2]), "sizes": row[3]}
        return {"error": f"Product '{clean_key}' not found in live database catalog rows."}
    except Exception as e:
        return {"error": f"Database pipeline disconnect anomaly: {str(e)}"}

def compute_dynamic_discount(product_key: str, coupon_code: str) -> dict:
    """Applies a database-validated coupon code to an item dynamically."""
    product = get_product_details(product_key)
    if "error" in product:
        return {"error": "Invalid item matching requested parameters"}
    
    try:
        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM discounts WHERE code = ? AND status = 'ACTIVE'", (str(coupon_code).upper().strip(),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            discount_percent = int(row[0])
            multiplier = (100 - discount_percent) / 100.0
            discounted_price = round(product["price"] * multiplier, 2)
            return {
                "success": True, 
                "message": f"Coupon applied! {discount_percent}% off regular pricing.",
                "price": discounted_price,
                "checkout_url": f"https://checkout.convertoai.shop/pay?item={product_key.lower().strip()}&discount={coupon_code.upper().strip()}"
            }
        return {"error": "Invalid or inactive discount coupon code."}
    except Exception as e:
        return {"error": f"Failed to compute discount table logic: {str(e)}"}

# --- ENDPOINTS ---

class ProductSchema(BaseModel):
    id: str
    name: str
    price: float
    stock: int
    sizes: str

class DiscountSchema(BaseModel):
    code: str
    rule: str
    value: int
    status: str

@app.get("/get-all-products")
async def get_all_products():
    try:
        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, stock, sizes FROM inventory")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "name": r[1], "price": r[2], "stock": r[3], "sizes": r[4]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-product")
async def add_product(product: ProductSchema):
    try:
        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO inventory (id, name, price, stock, sizes) VALUES (?, ?, ?, ?, ?)",
            (product.id.lower().strip(), product.name, product.price, product.stock, product.sizes)
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Product saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-all-discounts")
async def get_all_discounts():
    try:
        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        cursor.execute("SELECT code, rule, value, status FROM discounts")
        rows = cursor.fetchall()
        conn.close()
        return [{"code": r[0], "rule": r[1], "value": r[2], "status": r[3]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-discount")
async def add_discount(discount: DiscountSchema):
    try:
        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO discounts (code, rule, value, status) VALUES (?, ?, ?, ?)",
            (discount.code.upper().strip(), discount.rule, discount.value, discount.status.upper())
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Campaign '{discount.code}' stored successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_infrastructure(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Empty text message string.")

    try:
        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM inventory")
        db_items = cursor.fetchall()
        
        cursor.execute("SELECT code, rule, value FROM discounts WHERE status = 'ACTIVE'")
        db_discounts = cursor.fetchall()
        conn.close()
        
        catalog_str = "\n".join([f"- Use key '{item[0]}' if the user mentions {item[1]} or variations of {item[0]}" for item in db_items])
        discount_str = "\n".join([f"- Code '{d[0]}': Apply this code when {d[1]} (Saves the customer {d[2]}%)" for d in db_discounts])
    except:
        db_items = []
        db_discounts = []
        catalog_str = "- 'jacket' (for the Premium Waterproof Blue Jacket)"
        discount_str = "- Code 'HACK26': Apply this code when customer mentions price concerns (Saves 15%)"

    system_prompt = f"""
    You are the flagship autonomous AI Commerce Agent for ConvertoAI.
    You have direct access to backend data tools to verify real-time catalog parameters from SQLite.
    
    IMPORTANT CATALOG INSTRUCTIONS:
    You are an agent for an expansive, changing store catalog. Do NOT assume you only sell jackets. 
    You have access to any item in this dynamic live catalog list:
    {catalog_str}
    
    Active operational dynamic promotional code markdown rules:
    {discount_str}
    
    Strict Execution Mandates:
    1. Always call the `get_product_details` tool using the exact catalog key string whenever a user asks about, requests, or mentions any item or product category.
    2. Read the tool output output payload context directly. If the tool reports that an item key does not exist or returns an error, inform the user clearly about what products are inside the dynamic catalog list.
    3. If an item is out of stock (stock is 0), inform them clearly and ask if they would like to be waitlisted.
    4. If conversion friction matches one of the defined active promotion rules above, run your `compute_dynamic_discount` tool.
    5. Always state clear pricing and information provided ONLY by your tools. Do not invent details.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=request.message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[get_product_details, compute_dynamic_discount],
                temperature=0.0,  # Zero temperature forces absolute accuracy and removes random behavior
            )
        )

        checkout_link = None
        user_message_lower = request.message.lower()
        
        # Smart dynamic checking link generation architecture
        matched_item = None
        for item_id, _ in db_items:
            if item_id in user_message_lower:
                matched_item = item_id
                break

        # Generate custom checkout URLs based on detected items and codes
        if matched_item:
            active_code = None
            for d in db_discounts:
                if d[0].lower() in user_message_lower:
                    active_code = d[0]
                    break
            
            if active_code or "checkout_url" in response.text:
                if not active_code and len(db_discounts) > 0:
                    active_code = db_discounts[0][0]
                checkout_link = f"https://checkout.convertoai.shop/pay?item={matched_item}&discount={active_code if active_code else 'NONE'}"
            elif any(k in user_message_lower for k in ["buy", "order", "want", "yes", "checkout", "purchase"]):
                checkout_link = f"https://checkout.convertoai.shop/pay?item={matched_item}"

        return {"status": "success", "response": response.text, "checkout_link": checkout_link}
    except Exception as e:
        return {"status": "error", "response": "Infrastructure synchronization pipeline disconnect.", "checkout_link": None}