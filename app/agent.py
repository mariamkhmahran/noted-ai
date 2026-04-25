from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from .db import NotedDB
from .tools import add_note, search_notes, update_note, delete_note, fetch_all

load_dotenv()

TOOLS = [add_note, search_notes, update_note, delete_note, fetch_all]
DANGEROUS_TOOLS = {"delete_note", "update_note"}
CONFIRMATION_WORDS = {"yes", "do it", "confirm", "yep", "sure"}

SYSTEM_PROMPT = """You are a friendly note-taking assistant.

Rules:
- If the user refers to a note without an ID, call search_notes or fetch_all first.
- If a user's request is ambiguous and multiple notes match, ask for clarification.
- Only call update_note or delete_note when you have a specific note_id.
- Be friendly and natural when responding to the user.
- Try to always use the notes as reference for your answer if a matching note exists.

Error Handling & Privacy:
- If a tool returns an error or no results, do not show technical details to the user.
- Handle technical failures internally and inform the user gracefully.
- Maintain a professional interface by keeping technical issues hidden.
"""

class NotedAgent:
    def __init__(self):
        llm = ChatOpenAI(model="gpt-5.4-mini")

        self.agent = create_agent(
            llm,
            tools=TOOLS,
            system_prompt=SYSTEM_PROMPT,
            middleware=[
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "delete_note": {"allowed_decisions": ["approve", "reject"]},
                        "update_note": {"allowed_decisions": ["approve", "reject"]},
                    },
                    description_prefix="Confirm action",
                )
            ],
            checkpointer=InMemorySaver(),
        )

        self._thread_id = "noted_session"
        self._config = {"configurable": {"thread_id": self._thread_id}}
        self._opening = (
            "Hey there! Memory getting crowded? I've got space. "
            "Tell me what you'd like to save or find."
        )

    def step(self, user_input: str) -> str:
        print(">> Thinking...")

        response = self.agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=self._config,
            version="v2",
        )

        # If the agent hit an interrupt (dangerous tool pending), ask the user
        if response.interrupts:
            interrupt = response.interrupts[0]
            action = interrupt.value["action_requests"][0]
            print(f"\n>> About to {action['name']} with: {action['args']}")
            user_decision = input(">> Confirm? (yes/no): ").strip().lower()

            if any(word in user_decision for word in CONFIRMATION_WORDS):
                # Resume with approval
                response = self.agent.invoke(
                    Command(resume={"decisions": [{"type": "approve"}]}),
                    config=self._config,
                    version="v2",
                )
            else:
                # Resume with rejection
                response = self.agent.invoke(
                    Command(resume={"decisions": [{"type": "reject", "message": "User cancelled the action."}]}),
                    config=self._config,
                    version="v2",
                )

        return response.value["messages"][-1].content

    def run(self):
        db = NotedDB()
        print(f"\n>> {self._opening}")

        while True:
            user_input = input("> ").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                db.close_connection()
                break

            reply = self.step(user_input)
            print(f"\n>> {reply}")