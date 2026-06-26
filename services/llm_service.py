import re
import json
import logging
import os
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from database import db

logger = logging.getLogger(__name__)

def get_llm(temperature=0.0):
    active_model = db.get_setting("active_model", "Qwen3:8B (Local)")
    
    if active_model.startswith("ChatGPT"):
        api_key = os.environ.get("OPENAI_API_KEY") or db.get_setting("openai_api_key", "")
        if api_key:
            logger.info("Using ChatGPT 5.5 Cloud (GPT-4o engine)...")
            return ChatOpenAI(
                model="gpt-4o",
                temperature=temperature,
                api_key=api_key
            )
        else:
            logger.warning("OpenAI API Key not found. Falling back to local Qwen3:8B for ChatGPT 5.5 simulation.")
            return ChatOllama(
                model="qwen3:8b",
                temperature=temperature,
                base_url="http://localhost:11434"
            )
    else:
        logger.info("Using Qwen3:8B Local model...")
        return ChatOllama(
            model="qwen3:8b",
            temperature=temperature,
            base_url="http://localhost:11434"
        )

def invoke_llm(prompt_template_str: str, variables: dict, temperature=0.0) -> str:
    try:
        llm = get_llm(temperature)
        prompt = PromptTemplate.from_template(prompt_template_str)
        formatted_prompt = prompt.format(**variables)
        response = llm.invoke(formatted_prompt)
        return response.content
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise e

def clean_json_response(text: str) -> str:
    """Extracts JSON substring if the LLM wrapped it in markdown code blocks or text."""
    text = text.strip()
    # Check if there is a json code block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    # Check for raw curly brace matching
    match_curly = re.search(r"(\{.*\})", text, re.DOTALL)
    if match_curly:
        return match_curly.group(1)
    return text

def generate_json(prompt_template_str: str, variables: dict, temperature=0.0) -> dict:
    raw_response = invoke_llm(prompt_template_str, variables, temperature)
    cleaned = clean_json_response(raw_response)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON: {cleaned}. Error: {e}")
        raise Exception(f"Failed to parse LLM JSON response: {e}. Raw response: {raw_response}")
