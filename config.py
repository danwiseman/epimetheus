import redis
import json
import os


ollama_base_url = os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434"
redis_host = os.environ.get("REDIS_HOST") or "localhost"
redis_port = int(os.environ.get("REDIS_PORT") or 6379)
redis_url = f"redis://{redis_host}:{redis_port}"

r = redis.Redis(host=redis_host, port=redis_port, db=0)


def get_user_config(user_id):
    # Retrieve the user's configuration from Redis using a prefix
    config = r.hgetall("users:{}".format(user_id))

    if not config:
        return {
            "ollamaUrl": ollama_base_url,
            "redisUrl": redis_url,
            "qdrandUrl": "not implemented",
            "modelForDefault": "llama3.1:latest",
            "defaultModelPrompt": "",
        }

    # Convert byte strings to regular strings and decode JSON values
    user_config = {k.decode(): json.loads(v.decode()) for k, v in config.items()}
    return user_config


def set_user_config(user_id, config):
    # Store the user's configuration in Redis using a prefix
    r.hmset("users:{}".format(user_id), {k: json.dumps(v) for k, v in config.items()})


def group_emoji_models(config):
    data = config
    new_data = {}
    emojiModels = []

    for key, value in data.items():
        if "-" in key and key.split("-")[-1].isdigit() and value != "":
            base_key = key.rsplit("-", 1)[0]
            index = int(key.rsplit("-", 1)[1])
            while len(emojiModels) <= index:
                emojiModels.append({})
            emojiModels[index][base_key] = value
        elif value != "":
            new_data[key] = value

    new_data["emojiModels"] = [
        populatedModel for populatedModel in emojiModels if populatedModel
    ]

    return new_data
