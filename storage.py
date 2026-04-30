import sqlite3
import os
from config import DB_PATH, DATA_DIR

def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coordinates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            device_type TEXT,
            position_type INTEGER,
            position_type_name TEXT,
            lon REAL,
            lat REAL,
            alt REAL,
            receive_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw_data BLOB
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nfc_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            device_type TEXT,
            timestamp BIGINT,
            nfc_number TEXT,
            receive_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw_data BLOB
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nfc_shoe_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nfc_number TEXT NOT NULL UNIQUE,
            shoe_name TEXT,
            shoe_code TEXT,
            status INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_coordinate(frame):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    device_id_str = frame['device_id'].decode('ascii', errors='ignore')
    
    cursor.execute('''
        INSERT INTO coordinates 
        (device_id, device_type, position_type, position_type_name, lon, lat, alt, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        device_id_str,
        frame['device_info']['device_type'],
        frame['position_type'],
        frame['position_type_name'],
        frame['lon'],
        frame['lat'],
        frame['alt'],
        frame['raw_data']
    ))
    
    conn.commit()
    conn.close()
    return cursor.lastrowid

def save_nfc_record(frame):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    device_id_str = frame['device_id'].decode('ascii', errors='ignore')
    
    cursor.execute('''
        INSERT INTO nfc_records 
        (device_id, device_type, timestamp, nfc_number, raw_data)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        device_id_str,
        frame['device_info']['device_type'],
        frame['timestamp'],
        frame['nfc_number'],
        frame['raw_data']
    ))
    
    conn.commit()
    conn.close()
    return cursor.lastrowid

def get_recent_coordinates(limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM coordinates 
        ORDER BY receive_time DESC 
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_nfc_records(limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM nfc_records 
        ORDER BY receive_time DESC 
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_shoe_by_nfc(nfc_number):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM nfc_shoe_map 
        WHERE nfc_number = ? AND status = 1
    ''', (nfc_number,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def add_shoe_mapping(nfc_number, shoe_name, shoe_code):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO nfc_shoe_map (nfc_number, shoe_name, shoe_code)
            VALUES (?, ?, ?)
        ''', (nfc_number, shoe_name, shoe_code))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        cursor.execute('''
            UPDATE nfc_shoe_map 
            SET shoe_name = ?, shoe_code = ?
            WHERE nfc_number = ?
        ''', (shoe_name, shoe_code, nfc_number))
        conn.commit()
        success = True
    except Exception as e:
        print(f"Error adding shoe mapping: {e}")
        success = False
    
    conn.close()
    return success

def init_test_data():
    add_shoe_mapping("NFC001", "铁鞋A001", "TX-A001")
    add_shoe_mapping("NFC002", "铁鞋A002", "TX-A002")
    add_shoe_mapping("NFC003", "铁鞋B001", "TX-B001")

init_db()
init_test_data()