from dotenv import load_dotenv
from openai import OpenAI

import json

load_dotenv()

def chat():
    client = OpenAI()
    
    chat_history = [{
        "role": "assistant", 
        "content": """Hey there! Memory getting crowded? I’ve got space. 
        Tell me what you’d like to save or find.
        """
    }]

    while True:
        last_message = chat_history[len(chat_history) - 1]
        print(f"\n>> {last_message['content']}")
        prompt = input(f"> ")
        if prompt == "exit":
            break

        chat_history += [{
            "role": "user",
            "content": prompt
        }]

        print(">> Thinking...")

        response = client.responses.create(
            model="gpt-5.4-mini",
            input=chat_history,
        )

        chat_history += [{
            "role": "assistant",
            "content": response.output_text
        }]    

if __name__ == "__main__":
    client = OpenAI()
    chat()

