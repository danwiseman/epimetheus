import os
import re
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage


# Define prompt models for easy access
prompt_models = {
    "CHAT": "llama3",
    "CODE": "deepseek-coder-v2:latest",
    "IMAGE": "stable",
}


def get_valid_messages(messages):
    if not messages:
        raise ValueError("No messages found in thread")

    return [
        set_message(message)
        for message in messages
        if is_mentioned(message) or is_bot(message)
    ]


def is_bot(message):
    return message.get("bot_id") and not message.get("client_msg_id")


def is_mentioned(message):
    is_mentioned = not is_bot(message) and message["text"].startswith("<@")
    return is_mentioned


def set_message(message):
    if is_bot(message):
        return AIMessage(content=message["text"])
    else:
        message_removed_mention = re.sub(r"<@.*?>", "", message["text"])
        return HumanMessage(content=message_removed_mention)


def get_response(prompts, prompt_model):
    response = None

    if prompt_model == prompt_models["IMAGE"]:
        # client = DallEAPIWrapper(
        #     n=1,
        #     model=prompt_model,
        #     api_key=os.getenv("OPENAI_API_KEY"),  # Default
        # )

        # image_prompt = " ".join(
        #     [
        #         message["text"]
        #         for message in prompts
        #         if isinstance(message, HumanMessage)
        #     ]
        # )
        # response = {"content": client.invoke(image_prompt)}
        response = None
    else:
        client = ChatOllama(model=prompt_model, base_url=os.environ["OLLAMA_BASE_URL"])
        response = client.invoke(prompts)

    return response
