import argparse
import asyncio
import os

import requests
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown

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


async def query_provider(client, model_, prompt, temperature_, context, print_length, style, console):
    try:
        console.print(f"[bold]Querying model [blue underline]{model_}[/blue underline] with temperature [blue underline]{temperature_}[/blue underline] ...[/bold]\n")
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=model_,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. You will respond to the user's queries in a concise yet informative and detailed, comprehensive manner. You will be meticulous, ensuring quality and accuracy in your responses. The user will ask you a singular question, and you will provide a single, completely comprehensive and all-encompassing response. You will not provide any information that is not relevant, and you will not invite the user to ask follow-up questions or prompts. You will answer the question, no more; you will not ask for clarification or suggest future steps (unless this is requested)."},
                {"role": "user", "content": prompt},
                {"role": "user", "content": context}
            ],
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

def summarisation(client, model_, temperature, responses, context, style, console):
    try:
        console.print(f"[bold]Summarising responses with model [blue underline]{model_}[/blue underline] and temperature [blue underline]{temperature}[/blue underline] ...[/bold]")
        response = client.chat.completions.create(
            model=model_,  
            messages=[
                {"role": "system", "content": "You are a helpful assistant. The user has sent a prompt to numerous models with different temperatures, and you have received the responses. Your task is to summarise the responses into a single, comprehensive, all-encompassing response that is concise yet informative and detailed. You will be meticulous, ensuring quality and accuracy in your response. You will not provide any information that is not relevant, and you will not invite the user to ask follow-up questions or prompts. You will ensure that all information from responses is verified and accurate (utilising the context provided if necessary) and then synthesing it into a single unified, homogenous response."},
                {"role": "user", "content": "Here are some responses to the same question from different models and temperatures: " + str(responses)},
                {"role": "user", "content": context}
            ],
        )

        return (response.choices[0].message.content)
    except Exception as e:
        console.print(f"[bold]Error summarising with model [blue underline]{model_}[/blue underline] and temperature [blue underline]{temperature}[/blue underline]:[/bold] [italic]{str(e)}[/italic]")
        return False

def parse():
    parser = argparse.ArgumentParser(description="Run the panel multi-model tool.")
    parser.add_argument("--key", type=str, help="API key for the provider (if unprovided, will use environment variable ZEN_API_KEY)")
    parser.add_argument("prompt", type=str, help="The prompt to send to the panel")
    parser.add_argument("--summary_model", type=str, help="The model to use for summarisation (default: first free model returned by the provider)")
    parser.add_argument("--summary_temperature", type=float, default=0.3, help="The temperature to use for summarisation (default: 0.3)")
    parser.add_argument("--timeout", type=int, default=240, help="The timeout for each model response in seconds (default: 240)")
    parser.add_argument("--print_length", type=int, default=100, help="The number of characters to print from each model's response (default: 100)")
    parser.add_argument('--num_temperatures', type=int, default=3, help='The number of different temperatures to query for each model (default: 3)')
    parser.add_argument('--max_temperature', type=float, default=1.0, help='The maximum temperature to query (default: 1.0)')
    parser.add_argument('--style', type=str, default = 'bold blue', help='Rich formatting style for system / tool messages')
    return parser.parse_args()

def get_free_models():
    r = requests.get('https://opencode.ai/zen/v1/models')
    if len(r.json()["data"]) == 0:
        raise Exception("No models found")
    free = [m["id"] for m in r.json()["data"] if m["id"].endswith("-free")]
    return free

async def panel(combinations, client, prompt, context, print_length, style, console):
    results = await asyncio.gather(*[query_provider(client, model, prompt, temperature, context, print_length, style, console) for model, temperature in combinations])
    return results

def main():
    context = find_context()
    combinations = [(model, temperature) for model in models for temperature in temperatures]
    responses = asyncio.run(panel(combinations, client, args.prompt, context, args.print_length, style, console))
    summary_model = args.summary_model if args.summary_model else models[0]
    summary = summarisation(client, summary_model, args.summary_temperature, responses, context, style, console)
    if summary:
        summary = Markdown(summary)
        console.print('\n \n \n \n')
        console.print(summary)
    else:
        console.print("[bold]No valid responses received from summary model. Unable to generate summary.[/bold]")
    return responses, summary

if __name__ == "__main__":
    args = parse()
    style = args.style
    api_key_ = args.key if args.key else os.getenv("ZEN_API_KEY")
    client = OpenAI(
        base_url="https://opencode.ai/zen/v1",
        api_key=api_key_,
        timeout=args.timeout
    )
    console = Console()
    console.print("[bold]Validating API key ...[/bold]")
    if not validate_key(client):
        console.print("[bold]Invalid API key. Please check your key and try again.[/bold]")
        exit()
    console.print("[bold]API key validated successfully.[/bold]\n")
    models = get_free_models()
    temperatures = [round(args.max_temperature / args.num_temperatures * i, 2) for i in range(1, args.num_temperatures+1)]
    responses, summary = main()
