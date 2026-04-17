import pytest
from app.db import NotedDB

# create a fresh database for each test, give it to the test, then clean it up afterward
@pytest.fixture
def db():
    db = NotedDB(":memory:")
    yield db
    db.close_connection()

def test_db___create_note(db):
    db.create("Test", "Hello world", ["tag1"])

    result = db.search(
        "SELECT * FROM Notes WHERE title = ?",
        ("Test",)
    )

    assert len(result) == 1
    assert result[0]["title"] == "Test"

def test_db___update_note(db):
    db.create("Old", "Body", ["a"])

    note = db.search("SELECT * FROM Notes", ())[0]

    db.update(note["id"], "New", "Updated body", ["b"])

    updated = db.search("SELECT * FROM Notes WHERE id = ?", (note["id"],))

    assert updated[0]["title"] == "New"
    assert updated[0]["body"] == "Updated body"

def test_db___delete_note(db):
    db.create("ToDelete", "Body", ["x"])

    note = db.search("SELECT * FROM Notes", ())[0]

    db.delete([note["id"]])

    result = db.search("SELECT * FROM Notes", ())

    assert len(result) == 0

def test_db___create_note_missing_body_error(db):
    """Verifies that the database catches NULL constraints on the body field."""

    result = db.create("Title Only", None, ["tag"])
    
    assert isinstance(result, dict)
    assert result["status"] == "ERROR"
    assert "Failed to create Note" in result["content"]

def test_db___update_non_existent_note_error(db):
    """Verifies that updating a non-existent ID raises the expected custom exception."""

    result = db.update(999, "New Title", "New Body", ["tag"])
    
    assert isinstance(result, dict)
    assert result["status"] == "ERROR"
    assert "Note not found" in result["content"]

def test_db___delete_invalid_type_id(db):
    """Verifies the delete method handles incorrect ID types without crashing the loop."""
    # Passing a string that doesn't exist to verify the "not found" logic
    results = db.delete(["invalid_id_format"])
    print(results)
    
    assert "Note invalid_id_format not found" in results[0]