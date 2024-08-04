import os
import requests
import pathlib
from slack_bolt import App
import re

from config import get_user_config
from slack_extension.ai import get_valid_messages

from langchain_core.messages import AIMessage

from ai.ai_client import AIClient


app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


class Event:
    def __init__(self, channel: str, ts: str, thread_ts: str = None):
        self.channel = channel
        self.ts = ts
        self.thread_ts = thread_ts


def post_image_message():
    pass


def send_gpt_response(event: Event, say, regenerate_response=False):
    from slackstyler import SlackStyler

    styler = SlackStyler()

    channel = event.channel
    ts = event.ts
    thread_ts = event.thread_ts if event.thread_ts else ts

    try:
        response = app.client.conversations_replies(channel=channel, ts=thread_ts)
        if not response["messages"]:
            raise Exception("No messages found in thread")

        # React to provide feedback to the user
        reaction = "thinking_face"
        if regenerate_response:
            reaction = "eyes"
            # app.client.reactions_remove(channel=channel, name="rocket", timestamp=ts)
        app.client.reactions_add(channel=channel, name=reaction, timestamp=ts)

        model, system_prompt = get_prompt_models_from_slack_emoji(
            response["messages"][0]["text"].replace("<@.*?>", "")
        )

        print(f"received '{response['messages'][0]['text']}'")

        prompts = get_valid_messages(response["messages"], system_prompt)

        # remove last AI Message
        if regenerate_response and isinstance(prompts[-1], AIMessage):
            prompts.pop()
            prompts.pop()

        slack_ai_client = AIClient(
            prompt_model=model, api_base_url=os.environ.get("OLLAMA_BASE_URL")
        )
        ai_response = slack_ai_client.get_response(prompts)

        if not ai_response:
            raise Exception("No response")

        if model == "imageModel":
            stream, filename = url_to_read_stream(ai_response.content)
            app.client.files_upload_v2(
                file=stream, filename=filename, thread_ts=ts, channel_id=channel
            )
        else:
            say(
                channel=channel,
                text=str(styler.convert(ai_response.content)),
                thread_ts=ts,
            )
            app.client.reactions_add(channel=channel, name="rocket", timestamp=ts)

    except Exception as e:
        say(
            channel=channel,
            text=f"<@{os.environ.get('SLACK_ADMIN_MEMBER_ID')}> Error: {str(e)}",
            thread_ts=ts,
        )


def send_reaction_response(event: Event, reaction: dict, say):
    reaction_emoji = reaction["emoji"]
    reaction_user = reaction["user"]
    reaction_to_user = reaction["to_user"]

    user_info = get_user_info(reaction_to_user)

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<@{reaction_user}>, I'm sorry this message wasn't what you were looking for :face_with_peeking_eye:. Would you like me to try again?",
            },
        },
        {"type": "divider"},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":melting_face: Regenerate Response",
                        "emoji": True,
                    },
                    "value": f"{event.ts}",
                    "action_id": "regenerate_response",
                }
            ],
        },
    ]

    # TODO: fix the hard coding of the bot name and the emoji
    if (
        reaction_emoji == "hankey"
        and user_info
        and user_info["real_name"] == "epimetheus"
    ):
        say(
            channel=event.channel,
            blocks=blocks,
            text=f"<@{reaction_user}>, I'm sorry this message wasn't what you were looking for :face_with_peeking_eye:. Would you like me to try again?",
            thread_ts=event.ts,
        )


def send_gpt_regeneration(event: Event, say):
    send_gpt_response(event=event, say=say, regenerate_response=True)


def get_prompt_models_from_slack_emoji(message_text: str):
    regex = r":(\w+):"
    matches = re.search(regex, message_text)
    config = get_user_config(1)
    if matches and matches[1] and config["emojiModels"]:
        emoji = matches[1].replace(":", "")
        selected_model = find_model(data=config["emojiModels"], emoji=emoji)
        selected_prompt = find_model_prompt(data=config["emojiModels"], emoji=emoji)
        if len(selected_prompt) > 0:
            selected_prompt = selected_prompt[0]
        else:
            selected_prompt = None
        if len(selected_model) > 0:
            return selected_model[0], selected_prompt
        else:
            print(f"{emoji} did not match a model")
            return config["modelForDefault"], config["defaultModelPrompt"]

    print("No emoji matched a model")
    return config["modelForDefault"], config["defaultModelPrompt"]


def find_model(data, emoji):
    return [item["modelForEmoji"] for item in data if item["emojiText"] == emoji]


def find_model_prompt(data, emoji):
    return [
        item["emojiModelPrompt"]
        for item in data
        if "emojiModelPrompt" in item and item["emojiText"] == emoji
    ]


def url_to_read_stream(url: str):
    response = requests.get(url, stream=True)
    filename = pathlib.Path(url).name
    return (response.raw, filename)


def get_user_info(user_id):
    return app.client.users_info(user=user_id).get("user")


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
