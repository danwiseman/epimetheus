import re
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


def get_valid_messages(messages, system_prompt):
    if not messages:
        raise ValueError("No messages found in thread")

    if system_prompt:
        messages.insert(0, {"type": "system", "text": system_prompt})

    return [
        set_message(message)
        for message in messages
        if is_system(message) or is_mentioned(message) or is_bot(message)
    ]


def is_bot(message):
    return message.get("bot_id") and not message.get("client_msg_id")


def is_mentioned(message):
    is_mentioned = not is_bot(message) and message["text"].startswith("<@")
    return is_mentioned


def is_system(message):
    if message["type"] == "system":
        return True
    return False


def set_message(message):
    if is_bot(message):
        return AIMessage(content=message["text"])
    elif is_system(message):
        return SystemMessage(content=message["text"])
    else:
        message_removed_mention = re.sub(r"<@.*?>", "", message["text"])
        return HumanMessage(content=message_removed_mention)
