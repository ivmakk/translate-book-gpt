import os
from typing import Any, Dict
from langchain.llms import BaseLLM
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages.ai import AIMessage
from langchain_openai.chat_models.base import BaseChatOpenAI

MAX_OUPUT_TOKENS = {
    'gpt-4o': 16_384,
    'gpt-4o-mini': 16_384,
    'o1-mini': 65_536,
    'claude-3-haiku-20240307': 4_096,
    'claude-3-5-haiku-20241022': 8_192,
    'claude-3-5-sonnet-20241022': 8_192,
    # https://ai.google.dev/gemini-api/docs/models/gemini
    'gemini-1.5-pro': 8_192,
    'gemini-1.5-flash': 8_192,
    'gemini-2.0-flash-exp': 8_192,
    'deepseek-chat': 8_192 # 8K on site, probably it's 8192
}


def get_api_key(model_vendor) -> str:
    if model_vendor == "openai":
        return os.getenv("OPENAI_API_KEY")
    elif model_vendor == "anthropic":
        return os.getenv("ANTHROPIC_API_KEY")
    elif model_vendor == "google":
        return os.getenv("GEMINI_API_KEY")
    elif model_vendor == "deepseek":
        return os.getenv("DEEPSEEK_API_KEY")
    else:
        raise ValueError(f"Unsupported model vendor: {model_vendor}")


def get_model(
    api_key: str, model_vendor="openai", model_name="gpt-4o-mini", temperature: float = 0.2
) -> BaseLLM:
    if model_vendor == "openai":
        max_tokens = MAX_OUPUT_TOKENS.get(model_name, 16_384)
        return ChatOpenAI(model_name=model_name, temperature=temperature, api_key=api_key, max_tokens=max_tokens)
    elif model_vendor == "anthropic":
        max_tokens = MAX_OUPUT_TOKENS.get(model_name, 4_096)
        return ChatAnthropic(model_name=model_name, temperature=temperature, api_key=api_key, max_tokens=max_tokens, stop=None)
    elif model_vendor == "google":
        max_tokens = MAX_OUPUT_TOKENS.get(model_name, 8_192)
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature, api_key=api_key, max_tokens=max_tokens)
    elif model_vendor == "deepseek":
        max_tokens = MAX_OUPUT_TOKENS.get(model_name, 8_192)
        return BaseChatOpenAI(model=model_name, temperature=temperature, api_key=api_key, max_tokens=max_tokens, openai_api_base='https://api.deepseek.com')
    else:
        raise ValueError(f"Unsupported model vendor: {model_vendor}")


def extract_response_text(response: AIMessage, model_vendor: str = 'openai') -> str:
    return response.content
