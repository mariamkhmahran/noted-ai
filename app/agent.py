from dotenv import load_dotenv
from openai import OpenAI
from .db import NotedDB
from .tools import add_note, search_notes, delete_note, update_note, fetch_all
import json

load_dotenv()

with open("app/tool_definitions.json", "r") as file:
    TOOLS = json.load(file)["TOOLS"]

class NotedAgent():
    def __init__(self):
        self.client = OpenAI()
        self.chat_history = [{
            "role": "assistant", 
            "content": """Hey there! Memory getting crowded? I've got space. 
            Tell me what you'd like to save or find.
            """
        }]

    def step(self, user_prompt=None):
        if user_prompt:
            self.chat_history += [{
                "role": "user",
                "content": user_prompt
            }]
            
            print(">> Thinking...")

        response = self.client.responses.create(
            model="gpt-5.4-mini",
            instructions="""
            You are a friendly note-taking assistant.

            Rules:
            - If the user refers to a note without an ID, call search_notes or fetch_all first.
            - If a user’s request is ambiguous and multiple notes match, ask for clarification.
            - Only call update_note or delete_note when you have a specific note_id.
            - Always confirm before deleting or updating a note.
            - Be friendly and natural when responding to the user.
            - Try to always use the notes as reference for you answer if a matching note exists.

            Error Handling & Privacy:
            - If a tool returns an error or no results, do not show technical details (e.g., SQL errors, tracebacks, or database IDs) to the user.
            - Handle technical failures internally. If a tool fails, simply inform the user that the request could not be completed or that no matching notes were found.
            - Maintain a professional interface by keeping technical "behind-the-scenes" issues hidden.
            """,
            input=self.chat_history,
            tools=TOOLS
        )

        agent_response = response.output[-1] 
        if agent_response != None and agent_response.type == "function_call":
            # If the agent responds with a tool call, excute the corresponding tool function
            tool_name = agent_response.name
            args = json.loads(agent_response.arguments)

            # If it belongs to dangerous actions, 
            # check if the last user message contained a 'yes' or a confirmation keyword
            if tool_name in ["delete_note", "update_note"]:
                last_user_msg = next((m for m in reversed(self.chat_history) if "role" in m and m["role"] == "user"), {})
                confirmation_words = ["yes", "do it", "confirm", "yep", "sure"]
                
                user_confirmed = any(("content" in last_user_msg and word in last_user_msg["content"].lower()) for word in confirmation_words)

                if not user_confirmed:
                    self.chat_history += [{
                        "role": "system",
                        "content": f"Please confirm the action with the user."
                    }]
                    return

            # excute tool call
            if tool_name == "search_notes":
                result = search_notes(**args)
            elif tool_name == "add_note":
                result = add_note(**args)
            elif tool_name == "update_note":
                result = update_note(**args)
            elif tool_name == "delete_note":
                result = delete_note(**args)
            elif tool_name == "fetch_all":
                result = fetch_all(**args)

            self.chat_history += [
                agent_response, 
                {
                    "call_id": agent_response.call_id,
                    "output": json.dumps(result),
                    "type": "function_call_output",
                }
            ]
                
        else:
            # If the agent responds with natural language (No tool call), add it to history
            self.chat_history += [{
                "role": "assistant",
                "content": response.output_text
            }]    


    def run(self):
        db = NotedDB()

        while True:
            # If the last generated message is from the LLM, then display it to user
            # Otherwise it could be a system message or the result of a function call
            last_generated_msg = self.chat_history[len(self.chat_history) - 1]
            user_prompt = None
            if "role" in last_generated_msg and last_generated_msg['role'] == "assistant":
                print(f"\n>> {last_generated_msg['content']}")
                user_prompt = input(f"> ")

                if user_prompt == "exit":
                    db.close_connection()
                    break

            self.step(user_prompt)