from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
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

            cls._instance.vector_store = Chroma(
                collection_name="notes",
                embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
                persist_directory="./app/chroma_db"
            )

        return cls._instance

    def create(self, title, body, tags):
        try:
            self.cursor.execute(
                "INSERT INTO Notes (title, body, tags) VALUES (?, ?, ?)",
                (title, body, json.dumps(tags))
            )
            self.connection.commit()
            note_id = self.cursor.lastrowid

            try:
                self.vector_store.add_texts(
                    texts=[f"{title} - {body} - {' '.join(tags)}"],
                    metadatas=[{"note_id": note_id}],
                    ids=[str(note_id)]
                )
            except Exception as e:
                # Rollback SQLite insert to keep stores in sync
                self.cursor.execute("DELETE FROM Notes WHERE ID = ?", (note_id,))
                self.connection.commit()
                raise e
            
            return {
                "status": "SUCCESS",
                "message": "Note Created Successfully"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Failed to create Note. {e}"
            }

    def search(
            self, 
            query: str = None, 
            top_k: int = 4, 
            start_date: str = None, 
            end_date: str = None,
            order: str = "ASC"
        ):

        try:
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()

            if query:
                # Semantic search via Chroma
                results = self.vector_store.similarity_search(query, k=top_k)
                note_ids = [int(r.metadata["note_id"]) for r in results]

                if not note_ids:
                    return []

                placeholders = ",".join("?" * len(note_ids))
                sql = f"SELECT * FROM Notes WHERE ID IN ({placeholders})"
                params = list(note_ids)
            else:
                # Fetch all
                sql = "SELECT * FROM Notes WHERE 1=1"
                params = []

            if start_date:
                sql += " AND created_at >= ?"
                params.append(start_date)
            if end_date:
                sql += " AND created_at <= ?"
                params.append(end_date)

            sql += f" ORDER BY created_at {order}"

            self.cursor.execute(sql, params)
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
                "message": e
            }
        finally:
            self.connection.row_factory = None # reset to default valu
            self.cursor = self.connection.cursor()
        
    def delete(self, note_id: str):
            try:
                self.cursor.execute(
                    "DELETE FROM Notes WHERE ID=?",
                    (note_id,)
                )
                rows_affected = self.cursor.rowcount
                
                if rows_affected > 0:
                    result = f"Note {note_id} deleted successfully"
                else:
                    result = f"Note {note_id} not found"

                self.connection.commit()

            except Exception as e:
                print(e)
                result = f"Faild to delete {note_id}, ERROR: {e}"
            
            print(result)
            return result

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
                return {
                "status": "SUCCESS",
                "message": "Note updated successfully"
                }
            else:
                raise Exception("Note not found")
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Failed to update note. {e}"
            }
        finally:
            self.connection.commit()

    def close_connection(self):
        return self.connection.close()