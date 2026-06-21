import argparse
import asyncio
import os

from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown

from context import find_context
from llm import get_free_models, panel, summarisation, validate_key


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
    parser.add_argument('--summarise_context', action='store_true', help='Whether to include the context in the summary prompt (default: False)')
    return parser.parse_args()


def main(client, console):
    context = find_context(client, console, True if args.summarise_context else False)
    combinations = [(model, temperature) for model in models for temperature in temperatures]
    responses = asyncio.run(panel(combinations, client, args.prompt, context, args.print_length, console, 'Panel Responses'))
    summary_model = args.summary_model if args.summary_model else models[0]
    summary = summarisation(client, summary_model, args.summary_temperature, responses, context, console)
    if summary:
        summary = Markdown(summary)
        console.print('\n \n \n \n')
        console.print(summary)
    else:
        console.print("[bold]No valid responses received from summary model. Unable to generate summary.[/bold]")
    return responses, summary

if __name__ == "__main__":
    args = parse()
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
    responses, summary = main(client, console)
