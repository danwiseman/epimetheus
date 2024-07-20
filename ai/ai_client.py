from langchain_community.chat_models import ChatOllama

# Define prompt models for easy access
PROMPT_MODELS = {
    "CHAT": "llama3",
    "CODE": "deepseek-coder-v2:latest",
    "IMAGE": "stable",
}


class AIClient:
    def __init__(
        self, prompt_model=PROMPT_MODELS["CHAT"], api_base_url="http://localhost:11434"
    ):
        self.prompt_model = prompt_model
        self.base_url = api_base_url

    def get_response(self, prompts):
        response = None

        if self.prompt_model == PROMPT_MODELS["IMAGE"]:
            # For image generation (example placeholder for DallEAPIWrapper)
            pass  # Implement actual logic here if needed
        else:
            client = ChatOllama(model=self.prompt_model, base_url=self.base_url)
            response = client.invoke(prompts)

        return response
