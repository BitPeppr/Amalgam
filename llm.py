import asyncio

import requests


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

async def query_provider(client, model_, prompt, temperature_, context, print_length, console, mode):
    try:
        console.print(f"[underline]{mode}[/underline]: [bold]Querying model [blue underline]{model_}[/blue underline] with temperature [blue underline]{temperature_}[/blue underline] ...[/bold]\n")
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

def summarisation(client, model_, temperature, responses, context, console):
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


def get_free_models():
    r = requests.get('https://opencode.ai/zen/v1/models')
    if len(r.json()["data"]) == 0:
        raise Exception("No models found")
    free = [m["id"] for m in r.json()["data"] if m["id"].endswith("-free")]
    return free

async def panel(combinations, client, prompt, context, print_length, console, mode):
    results = await asyncio.gather(*[query_provider(client, model, prompt, temperature, context, print_length, console, mode) for model, temperature in combinations])
    return results



