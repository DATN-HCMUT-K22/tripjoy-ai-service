import time
from dataclasses import dataclass
from openai import OpenAI


@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str
    model: str = "openai/gpt-4o-mini"
    base_url: str = "https://openrouter.ai/api/v1"
    timeout_seconds: float = 90.0


class OpenRouterClient:
    def __init__(self, config: OpenRouterConfig):
        self._config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout_seconds,
        )

    def _call_with_retry(self, **kwargs):
        for attempt in range(3):
            try:
                return self._client.chat.completions.create(**kwargs)
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(1.5 * (attempt + 1))

    def run_llm(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
    ) -> str:
        resp = self._call_with_retry(
            model=self._config.model,
            temperature=temperature,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        content = resp.choices[0].message.content

        if not content:
            raise ValueError("Empty response from model")

        return content.strip()
