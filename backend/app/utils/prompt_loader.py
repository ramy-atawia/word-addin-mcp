"""
Utility functions for loading prompts from files.
"""
import os
from pathlib import Path


def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt from the prompts directory.
    
    Args:
        prompt_name (str): Name of the prompt file (without .txt extension)
        
    Returns:
        str: The prompt content
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    # Get the directory where this file is located
    current_dir = Path(__file__).parent
    prompts_dir = current_dir.parent / "prompts"
    prompt_file = prompts_dir / f"{prompt_name}.txt"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()


def load_prompt_template(prompt_name: str, **kwargs) -> str:
    """
    Load a prompt template and format it with the provided variables.
    
    Args:
        prompt_name (str): Name of the prompt file (without .txt extension)
        **kwargs: Variables to format into the prompt template
        
    Returns:
        str: The formatted prompt content
    """
    prompt_content = load_prompt(prompt_name)
    return prompt_content.format(**kwargs)
