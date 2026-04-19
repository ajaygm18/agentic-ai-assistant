from __future__ import annotations

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import get_settings


def get_chat_model(model: str | None = None, temperature: float | None = None) -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=model or settings.llm_model,
        api_key=settings.openai_api_key,
        base_url=settings.llm_base_url,
        temperature=settings.llm_temperature if temperature is None else temperature,
        max_retries=2,
    )


def get_planner_model() -> ChatOpenAI:
    settings = get_settings()
    return get_chat_model(model=settings.planner_model, temperature=0)


def get_embeddings() -> OpenAIEmbeddings:
    settings = get_settings()
    kwargs = {
        "model": settings.embedding_model,
        "api_key": settings.embedding_api_key or settings.openai_api_key,
        "check_embedding_ctx_length": False,
    }
    if settings.embedding_base_url:
        kwargs["base_url"] = settings.embedding_base_url
    return OpenAIEmbeddings(**kwargs)
