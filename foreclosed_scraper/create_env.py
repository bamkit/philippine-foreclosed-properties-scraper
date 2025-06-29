#!/usr/bin/env python3
"""Utility script to create a .env file with API keys."""

import os
import sys
from pathlib import Path
import shutil

def create_env_file():
    """Create a .env file with API keys."""
    script_dir = Path(__file__).parent.absolute()
    env_example_path = script_dir / "env.example"
    env_path = script_dir / ".env"
    
    # Check if env.example exists
    if not env_example_path.exists():
        print(f"Error: {env_example_path} not found.")
        return False
    
    # Check if .env already exists
    if env_path.exists():
        overwrite = input(".env file already exists. Overwrite? (y/n): ")
        if overwrite.lower() != "y":
            print("Aborted. Existing .env file was not modified.")
            return False
    
    # Copy example file
    shutil.copy(env_example_path, env_path)
    
    # Get API keys from user
    openai_key = input("Enter your OpenAI API key: ").strip()
    tavily_key = input("Enter your Tavily API key: ").strip()
    
    # Read the current content
    with open(env_path, "r") as f:
        content = f.read()
    
    # Replace the API keys
    content = content.replace("your_openai_api_key_here", openai_key)
    content = content.replace("your_tavily_api_key_here", tavily_key)
    
    # Write the updated content
    with open(env_path, "w") as f:
        f.write(content)
    
    print(f".env file created at {env_path}")
    return True


if __name__ == "__main__":
    create_env_file() 