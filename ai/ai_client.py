import os
from langchain_community.chat_models import ChatOllama

# Define prompt models for easy access
prompt_models = {
    "CHAT": "llama3",
    "CODE": "deepseek-coder-v2:latest",
    "IMAGE": "stable",
}


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
