from datetime import datetime, time
from langchain_core.tools import tool
from .db import NotedDB

@tool
def add_note(title, body, tags):
    """
    Creates a new note in the database.
    
    Args:
        title (str): The brief title of the note.
        body (str): The main content of the note (Required).
        tags (list[str]): A list of categories to label the note.
        
    Returns:
        dict: with a status (ERROR | SUCCESS) and message.
    """

    db = NotedDB()
    results = db.create(title, body, tags)

    return results

def validate_date_yyyy_mm_dd(date_str):
    """
    Validates if a string matches the YYYY-MM-DD date format.
    
    Args:
        date_str (str): The date string to validate.
        
    Returns:
        bool: True if valid, False otherwise.
    """

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except:
        return False

@tool
def search_notes(keyword=None, tags=[], start_date=None, end_date=None, limit=20):
    """
    Searches for notes based on keywords, tags, and date ranges.
    
    Args:
        keyword (str, optional): Search term for title or body.
        tags (list[str], optional): Filter for notes containing these tags.
        limit (int, optional): Max results to return (default 20).
        start_date (str, optional): Start date in YYYY-MM-DD format.
        end_date (str, optional): End date in YYYY-MM-DD format.
        
    Returns:
        list[dict]: Matching notes or dict: Error status and message.
    """

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

    if start_date:
        if not validate_date_yyyy_mm_dd(start_date):
            return {
                "status": "ERROR",
                "content": "Invalid start date format. Please use YYYY-MM-DD"
            }
        
        date_limits.append("created_at >= ?")
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        start_of_day = datetime.combine(start_datetime, time.min)
        params.append(start_of_day.strftime("%Y-%m-%d %H:%M:%S"))

    if end_date:
        if not validate_date_yyyy_mm_dd(end_date):
            return  {
                "status": "ERROR",
                "content": "Invalid end date format. Please use YYYY-MM-DD"
            }
        
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

    return results

@tool
def delete_note(ids):
    """
    Permanently removes notes from the database by ID.
    
    Args:
        ids (list[int]): A list of one or more Note IDs to delete.
        
    Returns:
        list[str]: A status message for each ID processed.
    """

    db = NotedDB()
    results = db.delete(ids)

    return results

@tool
def update_note(note_id, title, body, tags):
    """
    Modifies an existing note's title, body, or tags.
    
    Args:
        note_id (int): The unique ID of the note to update.
        title (str): The new title.
        body (str): The new content.
        tags (list[str]): The new list of tags.
        
    Returns:
        dict: with a status (ERROR | SUCCESS) and message.
    """

    db = NotedDB()
    results = db.update(note_id, title, body, tags)

    return results

@tool
def fetch_all(limit=None, order="ASC"):
    """
    Retrieves all notes from the database, sorted by creation date.
    
    Args:
        limit (int, optional): Maximum number of notes to retrieve.
        order (str, optional): Sort order, "ASC" or "DESC" (default "ASC").
        
    Returns:
        list[dict]: List of all notes found or dict: Error status and message.
    """

    query = f"""
    SELECT * 
    FROM Notes
    ORDER BY created_at {order}
    """

    if limit:
        query += " LIMIT ?"

    db = NotedDB()
    results = db.search(query, (limit,) if limit else ())

    return results

    