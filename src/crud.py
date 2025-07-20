import sqlite3

DB_PATH = "database.db"

def create_table(table: str, columns: dict):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        col_defs = ', '.join([f"{col} {tipo}" for col, tipo in columns.items()])
        query = f"CREATE TABLE IF NOT EXISTS {table} ({col_defs})"
        cursor.execute(query)
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"[ERROR - create_table] {e}")
    finally:
        conn.close()

def create(table: str, data: dict):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' for _ in data)
        values = tuple(data.values())
        cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"[ERROR - create] {e}")
    finally:
        conn.close()

def read(table: str, conditions: dict = None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if conditions:
            where = ' AND '.join(f"{k}=?" for k in conditions)
            values = tuple(conditions.values())
            cursor.execute(f"SELECT * FROM {table} WHERE {where}", values)
        else:
            cursor.execute(f"SELECT * FROM {table}")
        results = cursor.fetchall()
        return results
    except sqlite3.OperationalError as e:
        print(f"[ERROR - read] {e}")
        return []
    finally:
        conn.close()

def read_custom(query: str, params: tuple = ()):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        return results
    except sqlite3.OperationalError as e:
        print(f"[ERROR - read_custom] {e}")
        return []
    finally:
        conn.close()

def update(table: str, data: dict, conditions: dict):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        set_clause = ', '.join(f"{k}=?" for k in data)
        where_clause = ' AND '.join(f"{k}=?" for k in conditions)
        values = tuple(data.values()) + tuple(conditions.values())
        cursor.execute(f"UPDATE {table} SET {set_clause} WHERE {where_clause}", values)
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"[ERROR - update] {e}")
    finally:
        conn.close()

def delete(table: str, conditions: dict):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        where_clause = ' AND '.join(f"{k}=?" for k in conditions)
        values = tuple(conditions.values())
        cursor.execute(f"DELETE FROM {table} WHERE {where_clause}", values)
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"[ERROR - delete] {e}")
    finally:
        conn.close()
