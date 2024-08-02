from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from slack_extension.ai import (
    get_valid_messages,
    is_bot,
    is_mentioned,
    is_system,
    set_message,
)

ai_message = {"bot_id": "an_id", "type": "assistant", "text": "I'm an AI message"}
system_prompt = "I'm a system message"
user_message = {"type": "user", "text": "<@BOTID> This is a user question"}
messages = [user_message, ai_message, user_message]


def test_get_valid_messages():
    assert len(get_valid_messages(messages, None)) == 3
    assert len(get_valid_messages(messages, system_prompt=system_prompt)) == 4
    assert isinstance(
        get_valid_messages(messages, system_prompt=system_prompt)[0], SystemMessage
    )


def test_is_bot():
    bot_message = {"bot_id": "an_id"}
    assert is_bot(bot_message)

    not_bot_message = {"client_msg_id": "client id"}
    assert not is_bot(not_bot_message)


def test_is_mentioned():
    assert is_mentioned({"text": "<@USERID>"})

    assert not is_mentioned({"text": "Hi Epimetheus..."})


def test_is_system():
    assert is_system({"type": "system"})

    assert not is_system({"type": "user"})


def test_set_message():
    ai_message = {"bot_id": "an_id", "text": "I'm an AI message"}
    system_message = {"type": "system", "text": "I'm a system message"}
    user_message = {"type": "user", "text": "<@BOTID> This is a user question"}

    assert isinstance(set_message(ai_message), AIMessage)
    assert isinstance(set_message(system_message), SystemMessage)
    assert isinstance(set_message(user_message), HumanMessage)

    assert set_message(user_message).content == " This is a user question"
