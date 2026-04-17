from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def run_llm_judge(transcript_path, goal):
    client = OpenAI()
    
    with open(transcript_path, "r") as f:
        transcript = f.read()
    
    prompt = f"""
    You are an expert QA Evaluator for a Note-Taking AI Agent.
    
    USER GOAL: {goal}
    
    TRANSCRIPT:
    {transcript}
    
    EVALUATION CRITERIA:
    1. Did the agent accurately capture the user's intent? 
    2. Did the agent ask for clarification if things were ambiguous? 
    3. Did the agent confirm before destructive actions?
    4. Was the tone friendly and natural?
    
    Provide a score out of 10 and a brief reasoning.
    Format: SCORE: [number] | REASONING: [text]
    """
    
    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    output = response.choices[0].message.content

    score = int(output.split("SCORE:")[1].split("|")[0].split("/")[0].strip())
    reasoning = output.split("REASONING:")[1].strip()
    
    return score, reasoning

def log_judge_review(scenario_id, name, score, reasoning, log_file="app/tests/logs/judge_evaluation_report.txt"):
    """Appends the LLM judge's review to a central evaluation report."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"--- EVALUATION: {scenario_id} - {name} ---\n")
        f.write(f"SCORE: {score}/10\n")
        f.write(f"REASONING: {reasoning}\n")
        f.write("-" * 50 + "\n\n")