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