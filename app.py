from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
)
import io
import redis
import os
import threading


from PIL import Image, ImageColor

from flask_bootstrap import Bootstrap5


from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from ai.ai_client import AIClient
from config import get_user_config, set_user_config, group_emoji_models

from slack_extension.chat import (
    send_gpt_response,
    Event,
    send_gpt_regeneration,
    send_reaction_response,
)


flask_app = Flask(__name__)
bootstrap = Bootstrap5(flask_app)

ollama_base_url = os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434"
redis_host = os.environ.get("REDIS_HOST") or "localhost"
redis_port = int(os.environ.get("REDIS_PORT") or 6379)
redis_url = f"redis://{redis_host}:{redis_port}"

r = redis.Redis(host=redis_host, port=redis_port, db=0)

ai_client = AIClient(
    prompt_model="llama3:latest",
    api_base_url=ollama_base_url,
    redis_url=redis_url,
)

system_prompt = "TODO: Add system prompt here"


##########
# Flask App Routes
##########


@flask_app.context_processor
def inject_dynamic_data():
    return dict(sidebar_chats={}, models=get_ai_models())


def get_ai_models():
    from ollama import Client

    client = Client(host=ollama_base_url)
    return client.list()


@flask_app.route("/", methods=["GET"])
def index():
    return render_template("admin.html", configuration=get_user_config(1))


@flask_app.route("/config", methods=["POST"])
def config():
    config = request.json
    # TODO: add some validation
    if config:
        set_user_config(1, config=group_emoji_models(config))
        return jsonify(success=True)
    return jsonify(success=False)


@flask_app.route("/image_generate")
def image_generate():
    image = Image.new("RGB", (256, 256), ImageColor.getrgb("gray"))
    image_io = io.BytesIO()
    image.save(image_io, "PNG")
    image_io.seek(0)
    return send_file(image_io, mimetype="image/png")


##########
# Slack App Routes
##########


slack_app = App(
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET") or None,
    token=os.environ.get("SLACK_BOT_TOKEN") or None,
)


@slack_app.event("app_mention")
def handle_message(body, say):
    event = Event(
        channel=body["event"]["channel"],
        ts=body["event"]["ts"],
        thread_ts=body["event"].get("thread_ts"),
    )
    send_gpt_response(event, say)


@slack_app.event("reaction_added")
def handle_message_reactions(body, say):
    body_event = body["event"]
    event = Event(
        channel=body_event["item"]["channel"],
        ts=body_event["item"]["ts"],
    )
    reaction_emoji = body_event["reaction"]
    reaction_user = body_event["user"]
    reaction_to_user = body_event["item_user"]
    send_reaction_response(
        event,
        reaction={
            "emoji": reaction_emoji,
            "user": reaction_user,
            "to_user": reaction_to_user,
        },
        say=say,
    )


@slack_app.action("regenerate_response")
def handle_regenerate_response(ack, body, say, logger):
    ack()
    logger.info(body)
    event = Event(
        channel=body["container"]["channel_id"],
        ts=body["container"]["message_ts"],
        thread_ts=body["container"].get("thread_ts"),
    )
    send_gpt_regeneration(event, say)
    # say(f"ok, I will regnerate ```{body}```")


def runFlask():
    flask_app.run(debug=True, use_reloader=False, host="0.0.0.0")


def runSlack():
    handler = SocketModeHandler(slack_app, os.environ["SLACK_APP_TOKEN"])
    handler.start()


if __name__ == "__main__":
    flask_thread = threading.Thread(target=runFlask)
    slack_thread = threading.Thread(target=runSlack)

    flask_thread.start()
    slack_thread.start()

    flask_thread.join()
    slack_thread.join()
