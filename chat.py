import sys
import os
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from src.core.openai_provider import OpenAIProvider
from src.agent.agent import ReActAgent
from src.tools.tools import TOOLS, execute_tool

def main():
    llm = OpenAIProvider(model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"), api_key=os.getenv("OPENAI_API_KEY"))
    tool_defs = [{"name": t["name"], "description": t["description"]} for t in TOOLS]
    agent = ReActAgent(llm, tools=tool_defs, max_steps=7)
    agent.tool_executor = execute_tool

    print("=" * 55)
    print("  TravelWise Agent - Chat Mode")
    print("  Gõ 'quit' hoặc 'exit' để thoát")
    print("=" * 55)

    while True:
        try:
            user_input = input("\n[BẠN] ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nTạm biệt!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "thoát"):
            print("Tạm biệt!")
            break

        print("\n[AGENT đang suy nghĩ...]\n")
        answer = agent.run(user_input)
        print(f"[AGENT]\n{answer}")

if __name__ == "__main__":
    main()
