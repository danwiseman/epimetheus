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
import json


from PIL import Image, ImageColor

from flask_bootstrap import Bootstrap5

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_community.chat_message_histories import RedisChatMessageHistory

from slack.events import check_and_process_event

app = Flask(__name__)
bootstrap = Bootstrap5(app)
r = redis.Redis(host="localhost", port=6379, db=0)


with open("app/prompts/momo-rin-persona.md", "r") as f:
    system_prompt = f.read()


@app.context_processor
def inject_dynamic_data():
    return dict(sidebar_chats=get_recent_chats())


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        chat_session = request.args.get("chat_session")
        if not chat_session:
            chat_session = str(uuid.uuid4())
            add_message_to_chat_history(chat_session, SystemMessage(system_prompt))

        return render_template(
            "chat.html",
            chat_history=chat_message_history(chat_session).messages,
            chat_session=chat_session,
        )
    else:
        content = request.json.get("message")
        chat_session = request.json.get("chat_session")
        add_message_to_chat_history(chat_session, HumanMessage(content))
        return jsonify(success=True)


@app.route("/slack/events", methods=["POST"])
async def slack_events():
    raw_body = request.get_data()
    body = json.loads(raw_body)
    # request_type = body["type"]
    return await check_and_process_event(body)


@app.route("/stream", methods=["GET"])
def stream():
    chat_session = request.args.get("chat_session")
    print(chat_session)

    def generate():
        assistant_response_content = ""

        messages = chat_message_history(chat_session).messages
        chat = ChatOllama(model="llama3", base_url="http://ollama.ai.local")

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


@app.route("/reset", methods=["POST"])
def reset_chat():
    global chat_history
    chat_history = []
    return jsonify(success=True)


@app.route("/image_generate")
def image_generate():
    image = Image.new("RGB", (256, 256), ImageColor.getrgb("gray"))
    image_io = io.BytesIO()
    image.save(image_io, "PNG")
    image_io.seek(0)
    return send_file(image_io, mimetype="image/png")


def chat_message_history(chat_session):
    return RedisChatMessageHistory(
        chat_session, url="redis://localhost:6379", key_prefix="message_history:"
    )


def add_message_to_chat_history(chat_session, message):
    return chat_message_history(chat_session).add_messages([message])


def generate_chat_title(messages):
    with open("app/prompts/title-creation-prompt.md", "r") as f:
        title_prompt = f.read()

    chat = ChatOllama(model="llama3", base_url="http://ollama.ai.local")

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


if __name__ == "__main__":
    app.run(debug=True)
