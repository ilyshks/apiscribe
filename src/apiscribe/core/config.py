"""Конфигурация APIScribe.

Определяет все настройки прокси-сервера с валидацией через Pydantic.
"""

from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import List
from dotenv import load_dotenv


load_dotenv()

class Config(BaseModel):
    """Конфигурация прокси-сервера."""
    
    target_url: HttpUrl  # Целевой API
    
    port: int = Field(
        8080,  # значение по умолчанию
        ge=1,  # порт должен быть >= 1
        le=65535,  # порт должен быть <= 65535
        description="Порт для прокси-сервера"
    )

    host: str = Field(
        "127.0.0.1",
        description="Хост для прокси-сервера"
    )
    
    timeout: int = Field(
        30,
        ge=1,
        description="Таймаут запроса в секундах"
    )
    
    max_body_size: int = Field(
        10 * 1024 * 1024,  # 10 MB
        ge=1024,  # минимум 1 KB
        description="Максимальный размер тела запроса в байтах"
    )
    
    analyze_all: bool = Field(
        True,
        description="Анализировать все запросы"
    )
    
    sample_rate: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Доля запросов для анализа (0.0 - 1.0)"
    )
    
    exclude_paths: List[str] = Field(
        default_factory=list,  # пустой список по умолчанию
        description="Пути для исключения из анализа"
    )
    
    log_level: str = Field(
        "INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR)$",
        description="Уровень логирования"
    )
    
    save_examples: bool = Field(
        True,
        description="Сохранять примеры запросов/ответов"
    )
    
    model_config = ConfigDict(
        env_prefix="APISCRIBE_",  # читать из переменных окружения
        validate_assignment=True   # проверять даже при изменении
    )
