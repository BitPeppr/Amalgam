import argparse
import os

import requests
from openai import OpenAI

from context import find_context


def validate_key(client):
    try:
        response = client.chat.completions.create(
            model="big-pickle",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is 2 + 2? Provide one number as the answer, and no other words or information."}
                ],
            temperature=0.0
            )
        if response.choices[0].message.content.strip() == "4":
            return True
        else:
            return False
    except Exception:
        return False


def query_provider(client, model_, prompt, temperature_, context):
    try:
        response = client.chat.completions.create(
            model=model_,  
            messages=[
                {"role": "system", "content": "You are a helpful assistant. You will respond to the user's queries in a concise yet informative and detailed, comprehensive manner. You will be meticulous, ensuring quality and accuracy in your responses. The user will ask you a singular question, and you will provide a single, completely comprehensive and all-encompassing response. You will not provide any information that is not relevant, and you will not invite the user to ask follow-up questions or prompts. You will answer the question, no more; you will not ask for clarification or suggest future steps (unless this is requested)."},
                {"role": "user", "content": prompt},
                {"role": "user", "content": context}
            ],
            temperature=temperature_
        )

        return (response.choices[0].message.content)
    except Exception:
        print(f"Error querying model {model_} with temperature {temperature_}: {str(Exception)}")
        return False

def summarisation(client, model_, temperature, responses, context):
    try:
        response = client.chat.completions.create(
            model=model_,  
            messages=[
                {"role": "system", "content": "You are a helpful assistant. The user has sent a prompt to numerous models with different temperatures, and you have received the responses. Your task is to summarise the responses into a single, comprehensive, all-encompassing response that is concise yet informative and detailed. You will be meticulous, ensuring quality and accuracy in your response. You will not provide any information that is not relevant, and you will not invite the user to ask follow-up questions or prompts. You will ensure that all information from responses is verified and accurate (utilising the context provided if necessary) and then synthesing it into a single unified, homogenous response."},
                {"role": "user", "content": "Here are some responses to the same question from different models and temperatures: " + str(responses)},
                {"role": "user", "content": context}
            ],
            temperature=temperature
        )

        return (response.choices[0].message.content)
    except Exception:
        print(f"Error summarising with model {model_} and temperature {temperature}: {str(Exception)}")
        return False

def parse():
    parser = argparse.ArgumentParser(description="Run the panel multi-model tool.")
    parser.add_argument("--key", type=str, help="API key for the provider (if unprovided, will use environment variable ZEN_API_KEY)")
    parser.add_argument("prompt", type=str, help="The prompt to send to the panel")
    parser.add_argument("--summary_model", type=str, help="The model to use for summarisation (default: first free model returned by the provider)")
    parser.add_argument("--summary_temperature", type=float, default=0.3, help="The temperature to use for summarisation (default: 0.3)")
    return parser.parse_args()

def get_free_models():
    r = requests.get('https://opencode.ai/zen/v1/models')
    if len(r.json()["data"]) == 0:
        raise Exception("No models found")
    free = [m["id"] for m in r.json()["data"] if m["id"].endswith("-free")]
    return free


def main():
    args = parse()
    api_key_ = args.key if args.key else os.getenv("ZEN_API_KEY")
    client = OpenAI(
        base_url="https://opencode.ai/zen/v1",
        api_key=api_key_
    )
    if not validate_key(client):
        print("Invalid API key. Please check your key and try again.")
        return
    models = get_free_models()
    temperatures = [0.0, 0.4, 0.8]
    context = find_context()
    responses = []
    for model in models:
        for temperature in temperatures:
            response = query_provider(client, model, args.prompt, temperature, context)
            responses.append((model, temperature, response))
    summary_model = args.summary_model if args.summary_model else models[0]
    summary = summarisation(client, summary_model, args.summary_temperature, responses, context)
    print(summary)

if __name__ == "__main__":
    main()
