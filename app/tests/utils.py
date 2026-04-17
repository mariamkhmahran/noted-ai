
import os

def wait_for_agent_response(agent):
    """
    Stochastic models are unpredectible and sometimes it takes a few cycles for the 
    model to reach a conclusion.
    This function waits a few cycles until the agent responds.
    """

    while "role" not in agent.chat_history[-1]:
        agent.step()


def export_chat_history(chat_history, file_name):
    """ Parses agent chat history to create a user-friendly transcript. """

    file_path = os.path.join("app/tests/transcripts", file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        for message in chat_history:
            role = message["role"] if "role" in message else None
            content = message["content"] if "content" in message else None

            if not role or not content:
                continue

            if role == "assistant":
                f.write(f"\n>> {content.strip()}\n")
            elif role == "user":
                f.write(f"\n> {content.strip()}\n")