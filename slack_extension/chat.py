import os
import requests
import pathlib
from slack_bolt import App
import re

from slack_extension.ai import (
    prompt_models,
    get_valid_messages,
    get_response,
)

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

emoji_to_model = {
    "camera": prompt_models["IMAGE"],
    "avocado": prompt_models["CODE"],
    "pizza": prompt_models["CHAT"],
}


class Event:
    def __init__(self, channel: str, ts: str, thread_ts: str = None):
        self.channel = channel
        self.ts = ts
        self.thread_ts = thread_ts


def post_image_message():
    pass


def send_gpt_response(event: Event, say):
    channel = event.channel
    ts = event.ts
    thread_ts = event.thread_ts if event.thread_ts else ts

    try:
        response = app.client.conversations_replies(channel=channel, ts=thread_ts)
        if not response["messages"]:
            raise Exception("No messages found in thread")

        # React to provide feedback to the user
        app.client.reactions_add(channel=channel, name="thinking_face", timestamp=ts)

        model = get_prompt_models_from_slack_emoji(
            response["messages"][0]["text"].replace("<@.*?>", "")
        )

        prompts = get_valid_messages(response["messages"])

        print(f"Using model {model}")

        ai_response = get_response(prompts, model)

        if not ai_response:
            raise Exception("No response")

        if model == prompt_models["IMAGE"]:
            stream, filename = url_to_read_stream(ai_response.content)
            app.client.files_upload_v2(
                file=stream, filename=filename, thread_ts=ts, channel_id=channel
            )
        else:
            say(channel=channel, text=str(ai_response.content), thread_ts=ts)
            app.client.reactions_add(channel=channel, name="rocket", timestamp=ts)

    except Exception as e:
        say(
            channel=channel,
            text=f"<@{os.environ.get('SLACK_ADMIN_MEMBER_ID')}> Error: {str(e)}",
            thread_ts=ts,
        )


def get_prompt_models_from_slack_emoji(message_text: str):
    regex = r":(\w+):"
    matches = re.search(regex, message_text)
    if matches and matches[1]:
        emoji = matches[1]
        print(f"Found emoji {emoji}")

    return prompt_models["CHAT"]


def url_to_read_stream(url: str):
    response = requests.get(url, stream=True)
    filename = pathlib.Path(url).name
    return (response.raw, filename)


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
