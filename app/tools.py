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
def search_notes(query, start_date=None, end_date=None):
    """
    Searches for notes based on keywords, tags, and date ranges.
    
    Args:
        query (str): Search term for title, body, or tags.
        tags (list[str], optional): Filter for notes containing these tags.
        start_date (str, optional): Start date in YYYY-MM-DD format.
        end_date (str, optional): End date in YYYY-MM-DD format.
        
    Returns:
        list[dict]: Matching notes or dict: Error status and message.
    """

    formatted_start_date = None
    formatted_end_date = None
    if start_date:
        if not validate_date_yyyy_mm_dd(start_date):
            return {
                "status": "ERROR",
                "content": "Invalid start date format. Please use YYYY-MM-DD"
            }
        
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        start_of_day = datetime.combine(start_datetime, time.min)
        formatted_start_date = start_of_day
    
    if end_date:
        if not validate_date_yyyy_mm_dd(end_date):
            return  {
                "status": "ERROR",
                "content": "Invalid end date format. Please use YYYY-MM-DD"
            }
        
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
        end_of_day = datetime.combine(end_datetime, time.max)
        formatted_end_date = end_of_day

    db = NotedDB()
    results = db.search(query, start_date=formatted_start_date, end_date=formatted_end_date)

    return results

@tool
def delete_note(id: int, title: str):
    """
    Permanently removes a note from the database by ID.
    
    Args:
        ids (int): The note ID to delete.
        title (str): The title of the note to delete.
        
    Returns:
        str: A status message.
    """

    db = NotedDB()
    results = db.delete(id)

    return results[0]

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
def fetch_all(order="ASC"):
    """
    Retrieves all notes from the database, sorted by creation date.
    
    Args:
        order (str, optional): Sort order, "ASC" or "DESC" (default "ASC").
        
    Returns:
        list[dict]: List of all notes found or dict: Error status and message.
    """

    db = NotedDB()
    results = db.search(order=order)

    return results

    