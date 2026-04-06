import os
import sys

# Fix Windows encoding for Vietnamese
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

load_dotenv()

from src.core.openai_provider import OpenAIProvider
from src.agent.chatbot import Chatbot
from src.agent.agent import ReActAgent
from test_cases import TEST_CASES


def get_provider():
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai")
    model = os.getenv("DEFAULT_MODEL", "gpt-4o")

    if provider_name == "openai":
        return OpenAIProvider(model_name=model, api_key=os.getenv("OPENAI_API_KEY"))
    elif provider_name == "google":
        from src.core.gemini_provider import GeminiProvider
        return GeminiProvider(model_name=model, api_key=os.getenv("GEMINI_API_KEY"))
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def run_chatbot():
    print("=" * 60)
    print("CHATBOT BASELINE")
    print("=" * 60)

    llm = get_provider()
    chatbot = Chatbot(llm)

    for tc in TEST_CASES:
        print(f"\n--- Test Case {tc['id']} [{tc['type']}] ---")
        print(f"[USER] {tc['query']}")
        print(f"[EXPECTED] {tc['expected_behavior']}")
        response = chatbot.run(tc["query"])
        print(f"[CHATBOT] {response}\n")


def run_agent():
    print("=" * 60)
    print("REACT AGENT")
    print("=" * 60)

    llm = get_provider()

    from src.tools.tools import TOOLS, execute_tool

    tool_defs = [{"name": t["name"], "description": t["description"]} for t in TOOLS]
    agent = ReActAgent(llm, tools=tool_defs, max_steps=5)
    agent.tool_executor = execute_tool

    for tc in TEST_CASES:
        print(f"\n--- Test Case {tc['id']} [{tc['type']}] ---")
        print(f"[USER] {tc['query']}")
        print(f"[EXPECTED] {tc['expected_behavior']}")
        response = agent.run(tc["query"])
        print(f"[AGENT] {response}\n")


if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "chatbot"

    if mode == "chatbot":
        run_chatbot()
    elif mode == "agent":
        run_agent()
    elif mode == "both":
        run_chatbot()
        print("\n\n")
        run_agent()
    else:
        print("Usage: python main.py [chatbot|agent|both]")
