# NotedAI

A command-line (CLI) chat-based system that lets a user manage personal notes entirely through natural language. The system interprets user intent to create and manage notes.

---

## Tech Stack

- **Core Logic:** Python 3.10+
- **LLM Integration:** OpenAI [gpt-5.4-mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini) (via tool-calling)
- **Persistence:** SQLite.
- **Testing:** Pytest.
- **Containerization:** Docker, Docker-compose.

---

### Getting Started

Follow these steps to set up and run the **NotedAI** app on your local machine.

#### 1. Prerequisites

- **Docker & Docker Compose**: Ensure Docker is installed and the Docker Daemon is running.
- **OpenAI API Key**: You will need a valid key to power the agent's reasoning.

#### 2. Installation & Setup

First, clone the repository and navigate into the project directory:

```bash
git clone https://github.com/mariamkhmahran/noted-ai.git
cd noted-ai
```

Next, create a `.env` file in the root directory and add your OpenAI API key:

```bash
cp .env.example .env
echo "OPENAI_API_KEY=your_actual_key_here" > .env
```

#### 3. Launching the App

Run the following command to build the environment and start the interactive CLI chat:

```bash
docker compose run --rm app
```

> Use `docker compose run --rm app` instead of `docker compose up` to enable full terminal interactivity (STDIN/TTY) for the chat loop.

---

## System Architecture

### 1. The Autonomous Chat Loop (`agent.py`)

The project is designed as a standalone, modular system. The `NotedAgent` class handles the entire conversational lifecycle:

- **Interface:** A clean console-based loop where the user provides natural language prompts.
- **Orchestration:** The agent manages the `chat_history`, maintaining state across multiple turns.
- **Tool Execution:** It autonomously determines when a tool is needed, executes the SQLite operation in the background, and integrates the result back into the conversation without exposing raw JSON/SQL to the user.
- **Graceful Exit:** Users can terminate the session at any time by typing `exit`.

### 2. Tooling & CRUD Mapping

The agent interacts with the persistence layer through tool calling. Each tool is mapped to a specific **CRUD** (Create, Read, Update, Delete) operation:

| Tool Name      | CRUD Operation | Description                                                                                               |
| :------------- | :------------- | :-------------------------------------------------------------------------------------------------------- |
| `add_note`     | **Create**     | Generates a new entry with a title, body, and tags.                                                       |
| `search_notes` | **Read**       | Queries the database using keywords or tags to find existing info.                                        |
| `update_note`  | **Update**     | Modifies the content or metadata of an existing note by ID.                                               |
| `delete_note`  | **Delete**     | Permanently removes a record by ID.                                                                       |
| `fetch_all`    | **Read**       | Fetches the full list of notes (up to a limit). Helpful with reasoning tasks that require multiple notes. |

> Full tools definitions in `app/tool_definitions.json`

### 3. Safety-First Tooling

Destructive tools like `delete_note` and `update_note` are wrapped in a **Confirmation Protocol**. The agent's system instructions strictly prohibit calling these tools until the user has provided a definitive "Yes" or "Confirm" in a follow-up turn.

### 4. Persistence Layer (`db.py`)

I utilized **SQLite** for lightweight, serverless persistence.

#### **The Singleton Pattern**

The `NotedDB` class implements a **Singleton Pattern**. This ensures that throughout the entire lifecycle of the application only one database connection instance exists. This is to avoid the need to open then close the connection after every tool call. The connection can be closed once when the user exits. This also prevents data inconsistency and file-lock issues during concurrent test runs.

#### **Schema Design**

The database includes a single `Notes` table:

- **`id` (INTEGER):** Primary key for unique identification and reliable updates.
- **`title` (TEXT):** Indexed for fast keyword searching.
- **`body` (TEXT):** Stores the core content of the note.
- **`tags` (JSON/TEXT):** Stored as a JSON string, allowing the agent to filter notes by multiple categories dynamically.
- **`created_at` (TIMESTAMP):** Automatically tracked to allow the agent to reason about "recent" or "old" notes.

---

## Evaluation Testing

This project uses a three-tier testing strategy managed via pytest: unit tests, state progression assertion tests, scenario testing with LLM as judge.

To run all tests:

```bash
python -m pytest
```

### 1. Unit tests (`app/tests/unit-tests/`)

These are deterministic tests that evaluate the basic building blocks of the application.

- **`test_db.py`**: Validates the SQLite persistence layer and CRUD operations.
- **`test_agent.py`**: Ensures the `NotedAgent` initializes correctly and processes basic natural language CRUD requests.

### 2. State-Based Scenario Tests (`test_scenario_assertion.py`)

These are integration tests that evaluate the agent's performance across multi-turn conversations by asserting the final state of the database.

- **Methodology**: The test simulates a sequence of user prompts (e.g., adding a note, then updating it, then deleting another).
- **Goal**: To verify that regardless of the agent's "word choice," the correct **tools** were called and the **SQLite database** reflects the expected final state.
- **Audit**: Full transcripts are saved to `/logs/` for manual review

### 3. LLM-as-a-Judge Evaluation (`test_scenario_llm_judge.py`)

Because AI behavior is stochastic, there will always a certain degree of randomness in the base model's behaviour which cannot guarantee normal assertion test to capture the full spectrum of behaviours.

- **Scenarios:**: A collection of scenarios are collected in `scenarios.json`. Each scenario contains an initial state for the database, and a list of user prompts aimed to test a high level behavior like: intent disambiguation, contradiction detection, or dangerous actions confirmations.
- **The Process**: For each complex scenario in `scenarios.json`, the full scenario is excuted, then a full transcript is exported to the `tests/logs/` directory.
- **The Judge**: A high-reasoning LLM (Also `gpt-5.4-mini`) reviews these transcripts against a specific goal. It scores the agent on **intent interpretation**, **clarification of ambiguity**, and **adherence to safety protocols**. The Judge gives a score between 0 and 10. The scenario is considered successfull if it scores above 7.
- **The Report**: All judge scores and remarks are consolidated into `judge_evaluation_report.txt`. This enables an extra layer of semantic auditing.

### Note:

> Because LLMs are inherently non-deterministic, sometimes, tests fail despite the agent acting as desired. This is because it is almost impossible to capture all possible outputs in simple assertion sentences.
> Using an LLM as a judge and keeping a log of all conversation logs helps add another layer of dynamic testing.

---

## Project Structure

- `app/main.py`: Main entry point to the app.
- `app/agent.py`: Chat logic and system prompt configuration.
- `app/db.py`: SQLite persistence layer.
- `app/tools.py`: Tool definitions for the LLM.
- `tests/*`: Tests.
- `tests/logs/`: Auto-generated transcripts of every test run for audit purposes.

---

## Required Behaviours Satisfied

- [x] **Add/Search/Update/Delete Notes:** Full CRUD capabilities via tool calls.
- [x] **Intent Disambiguation:** Asks for clarification when queries return multiple results.
- [x] **Safety:** Mandatory confirmation on all destructive actions.
- [x] **Reasoning:** Capable of comparing notes and performing complex tasks (e.g., summerizing, identifying contradictions)
- [x] **Persistence:** All notes survive across restarts via local SQLite3 database.
- [x] **Multi-turn awareness:** By mainting the full chat history, the agent can handle follow up questions.
