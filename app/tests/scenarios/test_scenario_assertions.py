import pytest
from unittest.mock import patch
from datetime import datetime
from app.db import NotedDB
from ..utils import wait_for_agent_response, export_chat_history

@pytest.fixture
def seeded_db(tmp_path):
    NotedDB._instance = None
    db = NotedDB(str(tmp_path / "seeded_test_notes.db"))
    
    db.create("Office Info", "The door code is 1234.", ["office"])
    db.create("Groceries", "Buy milk and eggs.", ["urgent", "grocery"])
    
    return db

def test_scenario_state_progression(seeded_db):
    """
    Comprehensive state-based assertion across 5 turns.
    Tests: Addition, Multi-turn Update, Contextual Correction, and Deletion.
    """

    with patch("app.tools.NotedDB", return_value=seeded_db):
        from app.agent import NotedAgent
        agent = NotedAgent()

        # TURN 1: Add two notes 
        agent.step("Add a note: 'Project A' with body 'Starts Monday'. Also add a note: 'Team Lunch' body 'Friday at 1pm'.")
        wait_for_agent_response(agent)

        agent.step("How many notes do I have now?")
        wait_for_agent_response(agent)
        
        notes = seeded_db.search("SELECT * FROM Notes")
        assert len(notes) == 4
        assert any(n['title'] == 'Project A' for n in notes)

        # TURN 2: Update the 'Team Lunch' note
        agent.step("Update the Team Lunch note to say 'Friday at 2pm'.")
        wait_for_agent_response(agent)
        agent.step("I confirm the update")
        wait_for_agent_response(agent)
        
        # check if the body changed
        lunch_note = seeded_db.search("SELECT * FROM Notes WHERE title = ?", ("Team Lunch",))[0]
        assert "2pm" in lunch_note['body']

        # TURN 3: Follow-up update to test 'Multi-turn awareness' 
        agent.step("Actually, make it Tuesday instead of Friday.")
        wait_for_agent_response(agent)
        agent.step("I confirm the update")
        wait_for_agent_response(agent)
        
        # Agent must realize we are still talking about 'Team Lunch'
        updated_lunch = seeded_db.search("SELECT * FROM Notes WHERE title = ?", ("Team Lunch",))[0]
        assert "Tuesday" in updated_lunch['body']

        # TURN 4: Delete the first note (The project note)
        agent.step("Delete the Project A note.")
        wait_for_agent_response(agent)
        agent.step("Yes, confirm deletion.")
        wait_for_agent_response(agent)
        
        notes_after_delete = seeded_db.search("SELECT * FROM Notes")
        assert len(notes_after_delete) == 3 
        assert not any(n['title'] == 'Project A' for n in notes_after_delete)
        assert any(n['title'] == 'Team Lunch' for n in notes_after_delete)

        # TURN 5: Summarize / Count (Answer questions about notes)
        agent.step("How many notes do I have left?")
        wait_for_agent_response(agent)
        
        assert "3" in agent.chat_history[-1]["content"] or "three" in agent.chat_history[-1]["content"].lower()

        export_chat_history(agent.chat_history, f"test_scenario_state_progression__{datetime.now()}.txt")