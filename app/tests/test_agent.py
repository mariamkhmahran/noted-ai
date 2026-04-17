import pytest
from unittest.mock import patch
from app.db import NotedDB
from .utils import wait_for_agent_response

@pytest.fixture
def empty_db(tmp_path):
    db_file = tmp_path / "test_notes.db"
    db = NotedDB(str(db_file))
    yield db
    db.close_connection()

@pytest.fixture
def seeded_db(tmp_path):
    # Reset Singleton for a clean test state
    NotedDB._instance = None
    db = NotedDB(str(tmp_path / "seeded_test_notes.db"))
    
    # Pre-seed with contradictory and standard notes
    db.create("Office Info", "The door code is 1234.", ["office"])
    db.create("Office Update", "The door code is 5678.", ["office"])
    db.create("Groceries", "Buy milk and eggs.", ["urgent", "grocery"])
    db.create("Team standup", "we agreed to move it to Tuesdays.", ["meetings"])
    
    return db

def test_agent___add_note_intent(empty_db):
    """Testing the ability to create new notes"""

    with patch("app.tools.NotedDB", return_value=empty_db):
        from app.agent import NotedAgent
        agent = NotedAgent()
        
        # Add a Basic note
        agent.step("Save a note about meeting: move to Tuesday. Tag it as meetings.")
        
        results = empty_db.search("SELECT * FROM Notes WHERE title LIKE ?", ("%meeting%",))
        assert len(results) > 0, "Expected to add a new note"

        # Confirm to the user that you added it
        agent.step()
        assert "role" in agent.chat_history[-1] and agent.chat_history[-1]["role"] == "assistant"

        # Add another Note
        agent.step("Save a note about to do list: solve test. Tag it as tests.")

        results = empty_db.search("SELECT * FROM Notes")
        assert "type" in agent.chat_history[-1] and agent.chat_history[-1]["type"] == "function_call_output"
        assert len(results) > 1, "Expected to add a new note"

        agent.step()
        assert "role" in agent.chat_history[-1] and agent.chat_history[-1]["role"] == "assistant"

def test_agent___get_note_intent(seeded_db):
    """Testing the ability to get a specific note or derive insights based on existing notes"""

    with patch("app.tools.NotedDB", return_value=seeded_db):
        from app.agent import NotedAgent
        agent = NotedAgent()

        results = seeded_db.search("SELECT * FROM Notes")
        assert len(results) == 4
        
        agent.step("What is on my groceries list?")

        # A tool should be called
        tool_calls = [m for m in agent.chat_history if getattr(m, 'type', None) == "function_call"]
        assert any(tc.name == "search_notes" or tc.name == "fetch_all"  for tc in tool_calls)

        agent.step()
        agent_response = agent.chat_history[-1]

        # The agent should display the correct data to the user
        assert "role" in agent_response and agent_response["role"] == "assistant"
        assert "content" in agent_response and "milk" in agent_response["content"].lower() and "eggs" in agent_response["content"].lower()

        # The agent should be able to search the DB and compare notes to find contradictions
        agent.step("""
                   Do I have any contradictory notes? 
                   If yes, answer with: YES followed by the category tag names of the notes. 
                   If no, answer with: NO.""")
        
        # A tool should be called
        tool_calls = [m for m in agent.chat_history if getattr(m, 'type', None) == "function_call"]
        assert any(tc.name == "fetch_all"  for tc in tool_calls)

        while "role" not in agent.chat_history[-1]:
            # Wait until the agent responds
            agent.step()
        
        # The agent should find a contradiction
        agent_response = agent.chat_history[-1]
        assert "YES" in agent_response["content"] and "office" in agent_response["content"], "Expected the agent to find a contradiction in the office door code note."

def test_agent___update_note_intent(seeded_db):
    """
    Testing that the agent requires confirmation before updating a note 
    and successfully updates it.
    """

    with patch("app.tools.NotedDB", return_value=seeded_db):
        from app.agent import NotedAgent
        agent = NotedAgent()

        agent.step("Update the note about the team standup. The meeting are now moved to Fridays.")
        
        # Search tool should be called
        tool_calls = [m for m in agent.chat_history if getattr(m, 'type', None) == "function_call"]
        assert any(tc.name == "search_notes" for tc in tool_calls)

        wait_for_agent_response(agent)
        agent_response = agent.chat_history[-1]
        results = seeded_db.search("SELECT * FROM Notes WHERE title LIKE ?", ("%Team standup%",))

        # Agent should confirm action
        assert agent_response["role"] == "assistant"
        assert "Tuesdays" in results[0]["body"], "Expected the agent to confirm update but the agent did not."

        agent.step("Confirm Note Update.")
        results = seeded_db.search("SELECT * FROM Notes WHERE title LIKE ?", ("%Team standup%",))

        assert len(results) > 0

        updated_note = results[0]
        assert "Fridays" in updated_note["body"], f"Expected 'Fridays' in note body, but found: {updated_note['body']}"

def test_agent_delete_note_with_confirmation(seeded_db):
    """
    Testing that the agent requires confirmation before deleting 
    and successfully removes the note from the DB.
    """
    with patch("app.tools.NotedDB", return_value=seeded_db):
        from app.agent import NotedAgent
        agent = NotedAgent()

        agent.step("Delete the note about the team standup.")

        # Search tool should be called
        tool_calls = [m for m in agent.chat_history if getattr(m, 'type', None) == "function_call"]
        assert any(tc.name == "search_notes" for tc in tool_calls)

        wait_for_agent_response(agent)
        agent_response = agent.chat_history[-1]

        results = seeded_db.search("SELECT * FROM Notes WHERE title LIKE ?", ("%Team standup%",))

        assert agent_response["role"] == "assistant"
        assert len(results) > 0, "Expected the agent to confirm before deletion but the agent did not."

        agent.step("Yes, I am sure. Please delete it.")

        wait_for_agent_response(agent)
        agent_response = agent.chat_history[-1]
        
        # A tool should be called
        tool_calls = [m for m in agent.chat_history if getattr(m, 'type', None) == "function_call"]
        assert any(tc.name == "delete_note" for tc in tool_calls)

        # Final DB State Check
        results = seeded_db.search("SELECT * FROM Notes WHERE title LIKE ?", ("%Team standup%",))
        assert len(results) == 0, "The note should have been removed from the database."
