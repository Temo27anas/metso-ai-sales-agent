"""CLI chat assistant for a mining-equipment salesperson.

Usage:
    python main.py               interactive chat
    python main.py --once "..."  answer one question and exit
    python main.py --debug       print each tool call
"""
import argparse
import sys

from openai import OpenAI, OpenAIError

from config import MODEL, REASONING_EFFORT
from prompts import SYSTEM_PROMPT
from tools import TOOLS, run_tool

MAX_TOOL_ROUNDS = 10


def answer(client: OpenAI, messages: list, debug: bool) -> str:
    """call the model, run requested tools, repeat until it gives a final answer"""
    for _ in range(MAX_TOOL_ROUNDS): # limit the number of tool calls to avoid infinite loops
        extra = {"reasoning_effort": REASONING_EFFORT} if REASONING_EFFORT else {}
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, **extra)
        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            return message.content or ""

        for call in message.tool_calls:
            if debug:
                print(f"[tool] {call.function.name}({call.function.arguments})", file=sys.stderr)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": run_tool(call.function.name, call.function.arguments),
            })
    return "Sorry, I couldn't finish that answer (too many tool calls)."


def ask(client: OpenAI, messages: list, question: str, debug: bool) -> str:
    """ask a question, run tools if needed, and return the answer"""
    messages.append({"role": "user", "content": question})
    try:
        return answer(client, messages, debug) # run the model and tools until it gives a final answer
    except OpenAIError as e:
        messages.pop()  # drop the unanswered question so history stays valid
        return f"[API error] {e}"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--once", metavar="QUESTION", help="answer one question and exit")
    parser.add_argument("--debug", action="store_true", help="print tool calls and arguments")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252

    try:
        client = OpenAI()
    except OpenAIError as e:
        sys.exit(f"Could not create OpenAI client: {e}\nSet OPENAI_API_KEY in .env")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if args.once:
        print(ask(client, messages, args.once, args.debug)) # answer one question and exit
        return

    print(f"Sales assistant ({MODEL}). Type 'exit' to quit.\n")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            print(f"\nAssistant: {ask(client, messages, question, args.debug)}\n")


if __name__ == "__main__":
    main()
