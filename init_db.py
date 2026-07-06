import sqlite3

def setup_database():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    
    # 1. Create Inventory Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id TEXT PRIMARY KEY,
            name TEXT,
            price REAL,
            stock INTEGER,
            sizes TEXT
        )
    ''')
    
    # 2. Create Discounts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS discounts (
            code TEXT PRIMARY KEY,
            rule TEXT,
            value INTEGER,
            status TEXT
        )
    ''')
    
    # Seed Inventory Data
    cursor.execute('DELETE FROM inventory')
    cursor.execute("INSERT INTO inventory VALUES ('jacket', 'Premium Waterproof Blue Jacket', 89.00, 4, 'S,M,L')")
    cursor.execute("INSERT INTO inventory VALUES ('shoes', 'HyperLight Running Shoes', 120.00, 0, '9,10')")
    
    # Seed Discount Data
    cursor.execute('DELETE FROM discounts')
    cursor.execute("INSERT INTO discounts VALUES ('HACK26', 'Customer mentions price objection or high budget resistance', 15, 'ACTIVE')")
    
    conn.commit()
    conn.close()
    print("🚀 Real SQL Database ('store.db') initialized with Inventory and Discount schemas!")

if __name__ == '__main__':
    setup_database()