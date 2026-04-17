import pytest
import os
import json

from app.agent import NotedAgent
from app.db import NotedDB
from ..utils import export_chat_history, wait_for_agent_response
from .llm_judge import run_llm_judge, log_judge_review

def seed_database(db_instance, initial_state):
    """Dynamically populates the DB with custom data for a specific scenario."""
    db_instance.cursor.execute("DELETE FROM Notes")
    
    for note in initial_state:
        # Using your existing create method
        db_instance.create(
            title=note.get("title", "Untitled"),
            body=note.get("body", ""),
            tags=note.get("tags", [])
        )
    db_instance.connection.commit()

@pytest.fixture(scope="session", autouse=True)
def clean_evaluation_report():
    """Wipes the evaluation report at the start of the test session."""
    report_path = "app/tests/logs/judge_evaluation_report.txt"
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=== EVALUATION REPORT ===\n")
        f.write(f"Session Started: {os.path.getmtime(report_path)}\n\n")

with open("app/tests/scenarios/scenarios.json", "r") as f:
    SCENARIOS = json.load(f)["evaluation_suite"]

@pytest.mark.parametrize("scenario", SCENARIOS)
def test_llm_judge_scenarios(scenario, tmp_path):
    db_file = tmp_path / "scenarios_test.db"
    db = NotedDB(str(db_file))

    # Seed the database with the scenario's custom state
    seed_database(db, scenario["initial_state"])
    
    agent = NotedAgent()
    
    for turn in scenario["turns"]:
        agent.step(turn)
        wait_for_agent_response(agent)
    
    # Save transcript to file
    file_name = f"{scenario['name']}.txt"
    log_path = f"app/tests/logs/{file_name}"
    os.makedirs("app/tests/logs", exist_ok=True)
    export_chat_history(agent.chat_history, file_name)
    
    # invoke the LLM Judge
    score, reasoning = run_llm_judge(log_path, scenario["goal"])

    log_judge_review(
        scenario_id=scenario["id"],
        name=scenario["name"],
        score=score,
        reasoning=reasoning
    )
    
    print(f"\nJudge Results for {scenario['name']}: {score}/10")
    print(f"Reasoning: {reasoning}")
    
    assert score >= 8 