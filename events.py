from flask import Flask
import redis.asyncio as redis

app = Flask(__name__)
redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)


# @app.route("/slack/events", methods=["POST"])
# async def slack_events():
#     raw_body = request.get_data()
#     body = json.loads(raw_body)
#     #request_type = body["type"]
