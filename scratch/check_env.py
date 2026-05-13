import os
import json
from pathlib import Path

def check_env():
    print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")
    print(f"OPEN_API_KEY: {os.getenv('OPEN_API_KEY')}")
    print(f"GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')}")
    print(f"DEFAULT_LLM_PROVIDER: {os.getenv('DEFAULT_LLM_PROVIDER')}")

if __name__ == "__main__":
    check_env()
