from langchain_community.chat_models import ChatOllama
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import BaseMessage

# Define prompt models for easy access
PROMPT_MODELS = {
    "CHAT": "llama3",
    "CODE": "deepseek-coder-v2:latest",
    "IMAGE": "stable",
}


class AIClient:
    def __init__(
        self,
        prompt_model=PROMPT_MODELS["CHAT"],
        api_base_url="http://localhost:11434",
        chat_session=None,
        system_prompt=None,
        redis_url="http://localhost:6789",
    ):
        self.prompt_model = prompt_model
        self.base_url = api_base_url
        self.redis_url = redis_url
        self.chat_session = chat_session
        self.system_prompt = system_prompt

    def get_response(self, prompts):
        response = None

        if self.prompt_model == PROMPT_MODELS["IMAGE"]:
            # For image generation (example placeholder for DallEAPIWrapper)
            pass  # Implement actual logic here if needed
        else:
            client = ChatOllama(model=self.prompt_model, base_url=self.base_url)
            response = client.invoke(prompts)

        return response

    def get_message_history(self):
        return RedisChatMessageHistory(
            self.chat_session, url=self.redis_url, key_prefix="message_history:"
        )

    def append_to_message_history(self, message):
        if type(message) != [BaseMessage]:
            message = [message]

        return self.get_message_history().add_messages(message)