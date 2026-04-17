from dotenv import load_dotenv
from openai import OpenAI
from .tools import add_note, search_notes, delete_note, update_note, fetch_all
import json

load_dotenv()
TOOLS = [
    {
        "type": "function",
        "name": "search_notes",
        "description": "Search for notes by keyword or tags. Use this when the user refers to notes without specifying an ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "The keyword text used in the SELECT statement",
                },   
                "tags": {
                    "type": "array",
                    "description": "A list of possible tags for the target note",
                    "items": {
                        "type": "string",
                    }
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of notes to return.",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20
                },
                "start_date": {
                    "type": "string",
                    "description": "Optional start of date range, inclusive. Format: 'YYYY-MM-DD' or 'YYYY-MM-DD'.",
                    "nullable": True
                    },
                "end_date": {
                    "type": "string",
                    "description": "Optional end of date range, inclusive. Format: 'YYYY-MM-DD' or 'YYYY-MM-DD'.",
                    "nullable": True
                },
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "fetch_all",
        "description": "Fetch all user notes from database",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of notes to return.",
                    "minimum": 1,
                    "maximum": 1000,
                    "nullable": True
                },
                "order": {
                    "type": "string",
                    "enum": ["ASC", "DESC"],
                    "description": "Direction of list order. Controls whether to fetch newest or oldest notes first.",
                    "nullable": True,
                    "default": "ASC"
                }
            },
        },
    },
    {
        "type": "function",
        "name": "add_note",
        "description": "Add a new note with a title, body text and category tags.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The title of the note",
                },
                "body": {
                    "type": "string",
                    "description": "The body text of the note",
                },
                "tags": {
                    "type": "array",
                    "description": "A set of tags or categories for the note content",
                    "items": {
                        "type": "string"
                    }
                },
            },
            "required": ["title", "body"],
        },
    },
    {
        "type": "function",
        "name": "update_note",
        "description": "Update an existing note. Requires a note_id obtained from search_notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "note_id": {"type": "integer"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["note_id"]
        }
    },
    {
        "type": "function",
        "name": "delete_note",
        "description": "Delete a note by its ID. Only call this after confirming with the user.",
        "parameters": {
            "type": "object",
            "properties": {
                "ids": {
                    "type": "array",
                    "description": "List of note ids to be deleted",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["note_id"]
        }
    }
]

class NotedAgent():
    def __init__(self):
        self.client = OpenAI()
        self.chat_history = [{
            "role": "assistant", 
            "content": """Hey there! Memory getting crowded? I’ve got space. 
            Tell me what you’d like to save or find.
            """
        }]

    def run(self):
        while True:
            # If the last generated message is from the LLM, then display it to user
            # Otherwise it could be a system message or the result of a function call
            message = self.chat_history[len(self.chat_history) - 1]
            if "role" in message and message['role'] == "assistant":
                print(f"\n>> {message['content']}")
                prompt = input(f"> ")
                if prompt == "exit":
                    break

                self.chat_history += [{
                    "role": "user",
                    "content": prompt
                }]

                print(">> Thinking...")

            # Generate a new response based on chat history so far
            response = self.client.responses.create(
                model="gpt-5.4-mini",
                instructions="""
                You are a note-taking assistant.

                Rules:
                - If the user refers to a note without an ID, call search_notes first.
                - If multiple notes match, ask the user for clarification.
                - Only call update_note or delete_note when you have a specific note_id.
                - Always confirm before deleting or updating a note.
                - Be concise and natural when responding to the user.
                """,
                input=self.chat_history,
                tools=TOOLS
            )

            agent_response = response.output[-1] 
            if agent_response != None and agent_response.type == "function_call":
                # If the agent responds with a tool call, excute the corresponding tool function
                args = json.loads(agent_response.arguments)
                
                if agent_response.name == "search_notes":
                    result = search_notes(**args)
                elif agent_response.name == "add_note":
                    result = add_note(**args)
                elif agent_response.name == "update_note":
                    result = update_note(**args)
                elif agent_response.name == "delete_note":
                    result = delete_note(**args)
                elif agent_response.name == "fetch_all":
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