from langchain_community.chat_models import ChatOllama
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import BaseMessage


class AIClient:
    def __init__(
        self,
        prompt_model="llama3:latest",
        api_base_url="http://localhost:11434",
        chat_session=None,
        system_prompt=None,
        redis_url="http://localhost:6379",
    ):
        self._prompt_model = prompt_model
        self._base_url = api_base_url
        self._redis_url = redis_url
        self._chat_session = chat_session
        self._system_prompt = system_prompt
        self._client = ChatOllama(model=self._prompt_model, base_url=self._base_url)

    @property
    def chat_client(self):
        return self._client

    @property
    def chat_session(self):
        return self._chat_session

    @chat_session.setter
    def chat_session(self, chat_session):
        if isinstance(chat_session, str):
            self._chat_session = chat_session
        else:
            raise ValueError("Name must be a string.")

    @property
    def prompt_model(self):
        return self._prompt_model

    @prompt_model.setter
    def prompt_model(self, prompt_model):
        if isinstance(prompt_model, str):
            self._prompt_model = prompt_model
        else:
            raise ValueError("Model must be a string")

    def get_response(self, prompts):
        response = None

        if self._prompt_model == "imageModel":
            # For image generation (example placeholder for DallEAPIWrapper)
            pass  # Implement actual logic here if needed
        else:
            response = self._client.invoke(prompts)

        return response

    def get_message_history(self):
        return RedisChatMessageHistory(
            self._chat_session, url=self._redis_url, key_prefix="message_history:"
        )

    def append_to_message_history(self, message):
        if type(message) != [BaseMessage]:
            message = [message]

        return self.get_message_history().add_messages(message)
