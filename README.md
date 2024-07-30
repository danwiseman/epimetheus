# Epimetheus
------------

<p align="center">
    <img height="32" width="32" src="https://cdn.simpleicons.org/slack" />
    <img height="32" width="32" src="https://cdn.simpleicons.org/redis" />
    <img height="32" width="32" src="https://cdn.simpleicons.org/langchain" />
    <img height="32" width="32" src="https://cdn.simpleicons.org/ollama" />
</p>

<img height="150" width="150" src="static/assets/images/epimetheus-avatar.jpg" />

## Overview
------------

Epimetheus is a Slack bot that integrates with local Language Models (LLMs), keeping AI interactions within the organization. It uses Slack Emojis to allow users to choose between different models, such as code-based or image-generating models.

## Features
------------

*   **Model selection**: Users can select from multiple LLMs using Slack Emojis, allowing them to choose the most suitable model for their task.
*   **Customized chat bot**: Epimetheus will soon incorporate AI tools and RAGs (Reusable Aggregations) to provide a fully customized chat experience for users.
*   **Custom prompts**: Per-model custom prompts based on the selected Emoji.

## Installation
---------------

Currently it is a bit of an involved installation. The requirements are a Redis instance, an Ollama instance,
a Slack App and permissions, and this app itself.

Included is a `epimetheus.kube.yaml` file and a `Containerfile`. It is set to run on Podman :seal:, but can easily be
run on Docker :whale:.

Build the Epimetheus Application using `podman build . -t epimetheus-app:latest` or the docker command.

Create a secrets file in the following format:

```yaml
apiVersion: v1
data:
  slack-app-token: base64-app-token
  slack-signing-secret: base64-signing-secret
  slack-bot-token: base64-bot-token
kind: Secret
metadata:
  creationTimestamp: null
  name: slack-app
```

Then you can run the application:

```bash
podman kube play epimetheus.secrets.yaml
podman kube play epimetheus.kube.yaml
```

## Plans
--------

Future features include:

*   **RAG support**: Local private documents supported in a RAG (Reusable Aggregation).
*   **Image generation**: Using Comfy UI to generate images based on user input.


<a href='https://ko-fi.com/V7V110K9YZ' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi1.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>
