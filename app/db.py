from typing import List
import sqlite3
import json

class NotedDB():
    _instance = None

    def __init__(self, db_path="app/notes.db"):
        pass

    
    def __new__(cls, db_path="app/notes.db"):
        """
        Singleton Pattern is used here to ensure that a single DB connection is used
        throughout the application. This is to avoid the need to open then close the
        connection after every tool call. The connection can be closed once when the
        user exits. This also facilitates testing.
        """

        if cls._instance is None:
            cls._instance = super().__new__(cls)

            # Initialize connection
            cls._instance.connection = sqlite3.connect(db_path, check_same_thread=False)
            cls._instance.cursor = cls._instance.connection.cursor()

            # Create the table if not exist
            cls._instance.cursor.execute("""CREATE TABLE IF NOT EXISTS Notes (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                body TEXT NOT NULL,
                tags JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""")
            cls._instance.connection.commit()
        return cls._instance

    def create(self, title, body, tags):
        try:
            self.cursor.execute(
                "INSERT INTO Notes (title, body, tags) VALUES (?, ?, ?)",
                (title, body, json.dumps(tags))
            )
            self.connection.commit()
            
            return "Note Created Successfully"
        except Exception as e:
            return {
                "status": "ERROR",
                "content": f"Failed to create Note. {e}"
            }

    def search(self, sql_query, params=()):
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
        except Exception as e:
            return {
                "status": "ERROR",
                "content": e
            }
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
                except Exception as e:
                    results += [f"Faild to delete {note_id}, ERROR: {e}"]
            
            self.connection.commit()

            return results

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
        except Exception as e:
            return {
                "status": "ERROR",
                "content": f"Failed to update note. {e}"
            }
        finally:
            self.connection.commit()

    def close_connection(self):
        return self.connection.close()