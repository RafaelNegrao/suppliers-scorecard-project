import sqlite3
import getpass
from datetime import datetime


DB_PATH = "database.db"



import sqlite3
import time

MAX_RETRIES = 5
RETRY_DELAY = 0.5  # segundos

def create(query: str, params: tuple = (), log_description: str = None):
    retries = 0
    while retries < MAX_RETRIES:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()
            cursor.execute("BEGIN")
            cursor.execute(query, params)
            conn.commit()

            if log_description:
                log_event(f"[CREATE] {log_description}")

            return
        except sqlite3.OperationalError as e:
            conn.rollback()
            if "database is locked" in str(e).lower():
                retries += 1
                time.sleep(RETRY_DELAY)
            else:
                log_event(f"[CREATE ERROR] {e} | Query: {query} | Params: {params}")
                return
        finally:
            conn.close()
    log_event(f"[CREATE ERROR] Database locked after {MAX_RETRIES} retries | Query: {query} | Params: {params}")



def update(query: str, params: tuple = ()):
    retries = 0
    while retries < MAX_RETRIES:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()
            cursor.execute("BEGIN")
            cursor.execute(query, params)
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            conn.rollback()
            if "database is locked" in str(e).lower():
                retries += 1
                time.sleep(RETRY_DELAY)
            else:
                log_event(f"[UPDATE ERROR] {e} | Query: {query} | Params: {params}")
                return
        finally:
            conn.close()
    log_event(f"[UPDATE ERROR] Database locked after {MAX_RETRIES} retries | Query: {query} | Params: {params}")



def delete(query: str, params: tuple = ()):
    retries = 0
    while retries < MAX_RETRIES:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()
            cursor.execute("BEGIN")
            cursor.execute(query, params)
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            conn.rollback()
            if "database is locked" in str(e).lower():
                retries += 1
                time.sleep(RETRY_DELAY)
            else:
                log_event(f"[DELETE ERROR] {e} | Query: {query} | Params: {params}")
                return
        finally:
            conn.close()
    log_event(f"[DELETE ERROR] Database locked after {MAX_RETRIES} retries | Query: {query} | Params: {params}")



def read(query: str, params: tuple = ()):
    conn = sqlite3.connect(DB_PATH, timeout=5)
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    except sqlite3.OperationalError as e:
        log_event(f"[READ ERROR] {e} | Query: {query} | Params: {params}")
        return []
    finally:
        conn.close()



def log_event(description: str):
    now = datetime.now()
    usuario = getpass.getuser()
    query = "INSERT INTO log_table (date, time, user, event) VALUES (?, ?, ?, ?)"
    params = (
        now.strftime("%Y-%m-%d"),
        now.strftime("%H:%M:%S"),
        usuario,
        description
    )
    create(query, params)




def buscar_logs() -> list[dict]:
    query = "SELECT date, time, user, event FROM log_table ORDER BY rowid DESC"
    rows = read(query)

    colunas = ["date", "time", "user", "event"]
    dados_formatados = []

    for row in rows:
        row_dict = dict(zip(colunas, row))
        try:
            data_original = row_dict["date"]
            data_formatada = datetime.strptime(data_original, "%Y-%m-%d").strftime("%d/%m/%Y")
            row_dict["date"] = data_formatada
        except Exception as e:
            pass

        dados_formatados.append(row_dict)

    return dados_formatados

    





    