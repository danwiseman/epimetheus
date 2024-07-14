import os
from langchain import ChatOllama, DallEAPIWrapper
from langchain.messages import HumanMessage

prompt_models = {
    "CHAT": "llama3",
    "CODE": "deepseek-coder-v2:latest",
    "IMAGE": "stable",
}


def get_messages_from_slack_messages(messages):
    if not messages:
        raise ValueError("No messages found in thread")

    return [message for message in messages if not is_not_mentioned(message)]


def is_not_mentioned(message):
    is_bot = message.get("bot_id") and not message.get("client_msg_id")
    is_not_mentioned = not is_bot and not message["text"].startswith("<@")
    return is_not_mentioned


def get_response_from_model(prompts, prompt_model):
    response = None
    if prompt_model == prompt_models["IMAGE"]:
        client = DallEAPIWrapper(
            n=1,
            model=prompt_model,
            api_key=os.getenv("OPENAI_API_KEY"),  # Default
        )

        image_prompt = " ".join(
            [
                message["text"]
                for message in prompts
                if isinstance(message, HumanMessage)
            ]
        )
        response = {"content": client.invoke(image_prompt)}
    else:
        client = ChatOllama(model=prompt_model)
        response = client.invoke(prompts)

    return response
