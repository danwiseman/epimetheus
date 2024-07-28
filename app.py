from flask import (
    Flask,
    render_template,
    request,
    send_file,
)
import io
import redis
import os
import threading
import json

from PIL import Image, ImageColor

from flask_bootstrap import Bootstrap5


from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from ai.ai_client import PROMPT_MODELS, AIClient

from slack_extension.chat import send_gpt_response, Event


flask_app = Flask(__name__)
bootstrap = Bootstrap5(flask_app)

ollama_base_url = os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434"
redis_host = os.environ.get("REDIS_HOST") or "localhost"
redis_port = int(os.environ.get("REDIS_PORT") or 6379)
redis_url = f"redis://{redis_host}:{redis_port}"

r = redis.Redis(host=redis_host, port=redis_port, db=0)

ai_client = AIClient(
    prompt_model=PROMPT_MODELS["CHAT"],
    api_base_url=ollama_base_url,
    redis_url=redis_url,
)

system_prompt = "TODO: Add system prompt here"


##########
# Flask App Routes
##########


@flask_app.context_processor
def inject_dynamic_data():
    return dict(sidebar_chats={})


def get_user_config(user_id):
    # Retrieve the user's configuration from Redis using a prefix
    config = r.hgetall("users:{}".format(user_id))

    if not config:
        return {
            "emoji_models": [{"id": 0, "emoji_id": "avocado", "model_id": "0"}],
            "default_model": "llama3.1:latest",
            "ollama_base_url": ollama_base_url,
        }  # Return a default

    # Convert byte strings to regular strings and decode JSON values
    user_config = {k.decode(): json.loads(v.decode()) for k, v in config.items()}
    return user_config


def set_user_config(user_id, config):
    # Store the user's configuration in Redis using a prefix
    r.hmset("users:{}".format(user_id), {k: json.dumps(v) for k, v in config.items()})


def get_ai_models():
    from ollama import Client

    client = Client(host=ollama_base_url)
    return client.list()


@flask_app.route("/", methods=["GET"])
def index():
    return render_template(
        "admin.html", configuration=get_user_config(1), models=get_ai_models()
    )


@flask_app.route("/config", methods=["POST"])
def config():
    config = request.json.get("config")
    # TODO: add some validation
    set_user_config(1, config=config)


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
