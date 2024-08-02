from ai.ai_client import AIClient


def test_init():
    test_client = AIClient(
        prompt_model="llama3.1:latest",
        api_base_url="http://localhost:11434",
        chat_session=None,
        system_prompt=None,
        redis_url="http://localhost:6379",
    )

    assert test_client.chat_session is None
    assert test_client.prompt_model == "llama3.1:latest"
