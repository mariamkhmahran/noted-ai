from typing import List
import sqlite3
import json

class NotedDB():
    def __init__(self):
        self.connection = sqlite3.connect("app/notes.db")
        self.cursor = self.connection.cursor()

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS Notes (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            body TEXT NOT NULL,
            tags JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")
            
        self.connection.commit()

    def create(self, title, body, tags):
        try:
            self.cursor.execute(
                "INSERT INTO Notes (title, body, tags) VALUES (?, ?, ?)",
                (title, body, json.dumps(tags))
            )
            self.connection.commit()
            
            return "Note Created Successfully"
        except:
            return "Failed to create Note"

    def search(self, sql_query, params):
        try:
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()

            self.cursor.execute(
                sql_query,
                params
            )
            rows = self.cursor.fetchall()
            self.connection.commit()

            results = [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "body": row["body"],
                    "tags": row["tags"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]

            
            return results
        except ValueError as e:
            return None
        finally:
            self.connection.row_factory = None # reset to default valu
            self.cursor = self.connection.cursor()
        
    def delete(self, ids: List[str]):
            results = []
            for note_id in ids:
                try:
                    self.cursor.execute(
                        "DELETE FROM Notes WHERE ID=?",
                        (note_id,)
                    )
                    rows_affected = self.cursor.rowcount
                    
                    if rows_affected > 0:
                        results += [f"Note {note_id} deleted successfully"]
                    else:
                        results += [f"Note {note_id} not found"]
                except:
                    results += [f"Faild to delete {note_id}"]
            
            self.connection.commit()

    def update(self, note_id, title, body, tags):
        try:
            self.cursor.execute(
                """
                UPDATE Notes 
                SET title=?, body=?, tags=?
                WHERE ID = ?""",
                (title, body, json.dumps(tags), note_id)
            )
            rows_affected = self.cursor.rowcount

            if rows_affected > 0:
                return "Note updated successfully"
            else:
                raise Exception("Note not found")
        except:
            return "Failed to update note"
        finally:
            self.connection.commit()

    def close_connection(self):
        return self.connection.close()