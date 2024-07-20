from flask import (
    Flask,
    render_template,
    request,
    Response,
    stream_with_context,
    jsonify,
    send_file,
)
import io
import redis
import uuid
import time
import os
import threading


from PIL import Image, ImageColor

from flask_bootstrap import Bootstrap5

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_community.chat_message_histories import RedisChatMessageHistory

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from ai.ai_client import PROMPT_MODELS, AIClient
from slack_extension.chat import send_gpt_response, Event

flask_app = Flask(__name__)
bootstrap = Bootstrap5(flask_app)

redis_host = os.environ.get("REDIS_HOST") or "localhost"
redis_port = int(os.environ.get("REDIS_PORT") or 6379)
redis_url = f"redis://{redis_host}:{redis_port}"

r = redis.Redis(host=redis_host, port=redis_port, db=0)

slack_app = App(
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    token=os.environ.get("SLACK_BOT_TOKEN"),
)

ollama_base_url = os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434"

system_prompt = "TODO: Add system prompt here"

ai_client = AIClient(
    prompt_model=PROMPT_MODELS["CHAT"],
    api_base_url=ollama_base_url,
    redis_url=redis_url,
)

##########
# Flask App Routes
##########


@flask_app.context_processor
def inject_dynamic_data():
    return dict(sidebar_chats=get_recent_chats())


@flask_app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@flask_app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        chat_session = request.args.get("chat_session")
        if not chat_session:
            ai_client.chat_session = str(uuid.uuid4())
            ai_client.append_to_message_history(message=SystemMessage(system_prompt))

        return render_template(
            "chat.html",
            chat_history=ai_client.get_message_history().messages,
            chat_session=ai_client.chat_session,
        )
    else:
        content = request.json.get("message")
        chat_session = request.json.get("chat_session")
        ai_client.chat_session = chat_session
        ai_client.append_to_message_history(message=HumanMessage(content))
        return jsonify(success=True)


@flask_app.route("/stream", methods=["GET"])
def stream():
    chat_session = request.args.get("chat_session")
    print(chat_session)

    def generate():
        assistant_response_content = ""

        messages = chat_message_history(chat_session).messages
        chat = ChatOllama(model="llama3", base_url=ollama_base_url)

        for chunk in chat.stream(messages):
            if chunk.content:
                assistant_response_content += chunk.content
                data = chunk.content.replace("\n", " <br> ")
                yield f"data: {data}\n\n"

        yield "data: finish_reason: stop\n\n"
        add_message_to_chat_history(chat_session, AIMessage(assistant_response_content))
        if not get_chat_title(chat_session):
            messages = chat_message_history(chat_session).messages
            add_chat_title(chat_session, generate_chat_title(messages))

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@flask_app.route("/reset", methods=["POST"])
def reset_chat():
    global chat_history
    chat_history = []
    return jsonify(success=True)


@flask_app.route("/image_generate")
def image_generate():
    image = Image.new("RGB", (256, 256), ImageColor.getrgb("gray"))
    image_io = io.BytesIO()
    image.save(image_io, "PNG")
    image_io.seek(0)
    return send_file(image_io, mimetype="image/png")


def chat_message_history(chat_session):
    return RedisChatMessageHistory(
        chat_session, url=redis_url, key_prefix="message_history:"
    )


def add_message_to_chat_history(chat_session, message):
    return chat_message_history(chat_session).add_messages([message])


def generate_chat_title(messages):
    with open("flask_app/prompts/title-creation-prompt.md", "r") as f:
        title_prompt = f.read()

    chat = ChatOllama(model="llama3", base_url=ollama_base_url)

    messages.append(HumanMessage(title_prompt))

    return chat.invoke(messages).content


def get_chat_title(chat_session):
    pattern = f"message_subjects:*:{chat_session}*"
    keys = r.scan_iter(match=pattern)

    for key in keys:
        components = key.decode().split(":")

        if components[2] == chat_session:
            return r.get(key).decode()

    return None


def add_chat_title(chat_session, chat_title):
    timestamp = int(time.time())
    key = f"message_subjects:{timestamp}:{chat_session}"

    return r.set(key, chat_title)


def get_recent_chats():
    now = int(time.time())
    one_week_ago = now - 60 * 60 * 24 * 7

    filtered_keys = []
    for key in r.scan_iter("message_subjects:*"):
        # Parse out the timestamp from the key name
        try:
            timestamp, _ = key.decode("utf-8").split(":", 1)[1].split(":")
            timestamp = int(timestamp)
        except (ValueError, IndexError):
            # Ignore keys that don't match the expected format
            continue

        # Check if the timestamp is within the last week
        if one_week_ago <= timestamp <= now:
            # Do something with the key and value here
            filtered_keys.append(key)

    recent_chats = []
    for key in filtered_keys:
        # Decode the key to a string and split it by colons
        components = key.decode().split(":")

        # Extract the timestamp, session ID, and chat title from the key and value
        timestamp = components[1]
        session_id = components[2]
        chat_title = r.get(key).decode()

        # Append a dictionary containing the extracted information to the recent_chats list
        recent_chats.append(
            {"timestamp": timestamp, "session_id": session_id, "chat_title": chat_title}
        )

    return recent_chats


##########
# Slack App Routes
##########


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
    handler = SocketModeHandler(slack_app, os.environ["SLACK_APP_TOKEN"])

    flask_thread = threading.Thread(target=runFlask)
    slack_thread = threading.Thread(target=runSlack)

    flask_thread.start()
    slack_thread.start()

    flask_thread.join()
    slack_thread.join()
