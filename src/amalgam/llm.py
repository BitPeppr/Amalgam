import asyncio
from json import JSONDecodeError

import requests
from openai import APIStatusError, AuthenticationError
from rich.live import Live
from rich.markdown import Markdown


def validate_key(client, model):
    try:
        client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is 2 + 2?"}
            ],
            temperature=0.0,
            max_tokens=5
        )
        return True
    except AuthenticationError:
        return False
    except APIStatusError as e:
        raise RuntimeError(f"API error: {e.status_code} - {e.response.text}") from e
    except (ConnectionError, TimeoutError, JSONDecodeError) as e:
        raise RuntimeError(f"Connection failed: {e}") from e

async def query_provider(client, model_, prompt, temperature_, context, conversation_history, print_length, console, mode):
    try:
        console.print(f"[underline]{mode}[/underline]: [bold]Querying model [blue underline]{model_}[/blue underline] with temperature [blue underline]{temperature_}[/blue underline] ...[/bold]\n")
        messages = [
            {"role": "system", "content": "You are a helpful assistant. You will respond to the user's queries in a concise yet informative and detailed, comprehensive manner. You will be meticulous, ensuring quality and accuracy in your responses. Focus exclusively on the most recent user prompt. Any context or conversation history provided is supplementary background only — do not let it distract from answering the current question. You will not provide any information that is not relevant, and you will not invite the user to ask follow-up questions or prompts. You will answer the question, no more; you will not ask for clarification or suggest future steps (unless this is requested)."},
            {"role": "user", "content": f"Context:\n{context}"},
        ]
        if conversation_history:
            messages.append({"role": "user", "content": f"Previous conversation:\n{conversation_history}"})
        messages.append({"role": "user", "content": f"Current question:\n{prompt}"})
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=model_,
            messages=messages,
        )
        console.print(f"[bold]Response from model [blue underline]{model_}[/blue underline] with temperature [blue underline]{temperature_}[/blue underline]:[/bold] [italic]{response.choices[0].message.content.split('\n')[0][: min(len(response.choices[0].message.content.split('\n')[0]), print_length)]} ...[/italic]\n")

        return (response.choices[0].message.content)
    except Exception as e:
        try: 
            detail = e.response.json()['error']['message']
        except Exception:
            detail = e
        console.print(f"[bold]Error querying model [blue underline]{model_}[/blue underline] with temperature [blue underline]{temperature_}[/blue underline]:[/bold] [italic]{detail}[/italic]\n")
        return False

def summarisation(client, model_, temperature, responses, console):
    try:
        console.print(f"[bold]Summarising responses with model [blue underline]{model_}[/blue underline] and temperature [blue underline]{temperature}[/blue underline] ...[/bold]")
        stream = client.chat.completions.create(
            model=model_,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. The user has sent a prompt to numerous models with different temperatures, and you have received the responses. Your task is to summarise the responses into a single, comprehensive, all-encompassing response that is concise yet informative and detailed. You will be meticulous, ensuring quality and accuracy in your response. You will not provide any information that is not relevant, and you will not invite the user to ask follow-up questions or prompts. You will synthesise the best information from the responses into a single unified, homogenous response."},
                {"role": "user", "content": "Here are some responses to the same question from different models and temperatures: " + str(responses)},
            ],
            stream=True,
        )
        full_content = ""
        with Live(console=console, refresh_per_second=12) as live:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_content += delta
                    live.update(Markdown(full_content))
        return full_content
    except Exception as e:
        console.print(f"[bold]Error summarising with model [blue underline]{model_}[/blue underline] and temperature [blue underline]{temperature}[/blue underline]:[/bold] [italic]{str(e)}[/italic]")
        return False


def get_free_models(base_url='https://opencode.ai/zen/v1'):
    r = requests.get(f'{base_url}/models')
    if len(r.json()["data"]) == 0:
        raise Exception("No models found")
    free = [m["id"] for m in r.json()["data"] if m["id"].endswith("-free")]
    return free

async def panel(combinations, client, prompt, context, conversation_history, print_length, console, mode):
    results = await asyncio.gather(*[query_provider(client, model, prompt, temperature, context, conversation_history, print_length, console, mode) for model, temperature in combinations])
    return results



