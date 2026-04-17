import sqlite3
import json
from datetime import datetime, time
from db import NotedDB

def add_note(title, body, tags):
    """ Add a new note to DB with a title, content, and category tags"""

    db = NotedDB()
    results = db.create(title, body, tags)
    db.close_connection()

    return results

def validate_date_yyyy_mm_dd(date_str):
    """Helper function to validate date limit inputs for the search function"""

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def search_notes(keyword=None, tags=[], limit=20, start_date=None, end_date=None):
    """Search notes in database based on criteria"""

    sql_query = "SELECT * FROM Notes WHERE 1=0"
    where_clauses = []
    params = []
    date_limits = []

    if keyword != None:
        where_clauses.append("(title LIKE ? OR body LIKE ?)")
        params += [f"%{keyword}%"] * 2

    for tag in tags:
        where_clauses.append("""
            EXISTS (
                SELECT 1 FROM json_each(Notes.tags)
                WHERE json_each.value = ?
            )
        """)
        params.append(f"%{tag}%")

    # join the previous conditions with OR inside parentheses (in case a date limit was enforced)
    where_sql = "(" + (" OR ".join(where_clauses) if where_clauses else "1=1") + ")"

    if start_date != None and validate_date_yyyy_mm_dd(start_date):
        date_limits.append("created_at >= ?")

        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        start_of_day = datetime.combine(start_datetime, time.min)
        params.append(start_of_day.strftime("%Y-%m-%d %H:%M:%S"))
    if end_date != None and validate_date_yyyy_mm_dd(end_date):
        date_limits.append("created_at <= ?")

        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
        end_of_day = datetime.combine(end_datetime, time.max)
        params.append(end_of_day.strftime("%Y-%m-%d %H:%M:%S"))

    if len(date_limits) > 0:
        where_sql += f" AND ({' AND '.join(date_limits)})"


    sql_query = f"""
        SELECT id, title, body, tags, created_at
        FROM Notes
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ?
    """
    params.append(limit)

    db = NotedDB()
    results = db.search(sql_query, params)
    db.close_connection()

    return results

def delete_note(ids):
    db = NotedDB()
    results = db.delete(ids)
    db.close_connection()

    return results

def update_note(note_id, title, body, tags):
    db = NotedDB()
    results = db.update(note_id, title, body, tags)
    db.close_connection()

    return results

def fetch_all(limit=None, order="ASC"):
    query = f"""
    SELECT * 
    FROM Notes
    ORDER BY created_at {order}
    """

    if limit:
        query += " LIMIT ?"

    db = NotedDB()
    results = db.search(query, (limit,))
    db.close_connection()

    return results

    