import os
from typing import Any, Dict
from langchain.llms import BaseLLM
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages.ai import AIMessage


def get_api_key(model_vendor) -> str:
    if model_vendor == "openai":
        return os.getenv("OPENAI_API_KEY")
    elif model_vendor == "anthropic":
        return os.getenv("ANTHROPIC_API_KEY")
    elif model_vendor == "google":
        raise NotImplementedError("Google model support is not implemented yet.")
    else:
        raise ValueError(f"Unsupported model vendor: {model_vendor}")


def get_model(
    api_key: str, model_vendor="openai", model_name="gpt-4o-mini", temperature: float = 0.2
) -> BaseLLM:
    if model_vendor == "openai":
        return ChatOpenAI(model_name=model_name, temperature=temperature, api_key=api_key)
    elif model_vendor == "anthropic":
        return ChatAnthropic(model_name=model_name, temperature=temperature, api_key=api_key, max_tokens=4096)
    elif model_vendor == "google":
        raise NotImplementedError("Google model support is not implemented yet.")
    else:
        raise ValueError(f"Unsupported model vendor: {model_vendor}")


def extract_response_text(response: AIMessage, model_vendor: str = 'openai') -> str:
    return response.content

    # if model_vendor == "openai":
    #     return response['choices'][0]['message']['content']
    # elif model_vendor == "anthropic":
    #     return response['completion']
    # elif model_vendor == "google":
    #     return response['candidates'][0]['output']
    # else:
    #     raise ValueError(f"Unsupported model vendor: {model_vendor}")