"""
EchoMind LLM Client
One provider-agnostic entry point for every AI engine.

Providers are tried in priority order. When one fails permanently (bad key, no
quota, no credit, server not running) it is retired for the life of the process
and the next provider takes over. When every provider is exhausted the engines
fall back to their local heuristics, so the app always answers.

Ollama runs models locally and costs nothing — it is the free path.
"""

from typing import List, Optional

import httpx

from app.core.config import settings

# Failure text that means "this will not work on retry".
_PERMANENT_MARKERS = (
    "quota",
    "credit balance",
    "billing",
    "insufficient_quota",
    "invalid api key",
    "invalid x-api-key",
    "authentication",
)

_PERMANENT_EXCEPTIONS = {
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
}


class LLMClient:
    """Text completion across Anthropic, OpenAI and Ollama."""

    def __init__(self):
        self._initialized = False
        self._chain: List[str] = []
        self._dead: set = set()
        self._anthropic = None
        self._openai = None

    # ── setup ────────────────────────────────────────────────────────────

    def initialize(self) -> None:
        """Build the provider chain. Safe to call repeatedly."""
        if self._initialized:
            return
        self._initialized = True

        forced = (settings.LLM_PROVIDER or "auto").strip().lower()
        order = [forced] if forced != "auto" else ["anthropic", "openai", "ollama"]

        for name in order:
            # A missing SDK drops that provider from the chain instead of
            # crashing startup — the next provider (usually Ollama) takes over.
            if name == "anthropic" and settings.ANTHROPIC_API_KEY:
                try:
                    from anthropic import AsyncAnthropic
                except ImportError as e:
                    print(f"  ⚠️ anthropic SDK not installed ({e}); skipping.")
                    continue
                self._anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                self._chain.append("anthropic")
            elif name == "openai" and settings.OPENAI_API_KEY:
                try:
                    from openai import AsyncOpenAI
                except ImportError as e:
                    print(f"  ⚠️ openai SDK not installed ({e}); skipping.")
                    continue
                self._openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                self._chain.append("openai")
            elif name == "ollama":
                # No key and no client object — reachability is probed on first
                # use, so a stopped Ollama simply drops out of the chain.
                self._chain.append("ollama")

        if self._chain:
            print(f"  🧠 LLM providers: {' → '.join(self._chain)}")
        else:
            print("  🧠 No LLM configured; engines will use local heuristics.")

    @property
    def provider(self) -> Optional[str]:
        """The provider that would serve the next call."""
        for name in self._chain:
            if name not in self._dead:
                return name
        return None

    @property
    def available(self) -> bool:
        return self.provider is not None

    def _retire(self, name: str, exc: Exception) -> None:
        self._dead.add(name)
        nxt = self.provider
        follow = f"falling back to {nxt}" if nxt else "using local heuristics"
        print(f"  ⚠️ LLM provider '{name}' unavailable ({type(exc).__name__}: {exc}); {follow}.")

    @staticmethod
    def _is_permanent(exc: Exception) -> bool:
        """True for failures that will not fix themselves on retry."""
        if type(exc).__name__ in _PERMANENT_EXCEPTIONS:
            return True
        msg = str(exc).lower()
        return any(marker in msg for marker in _PERMANENT_MARKERS)

    # ── public API ───────────────────────────────────────────────────────

    async def complete(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
        system: Optional[str] = None,
    ) -> str:
        """Single-prompt completion. Returns "" when no provider can serve it."""
        messages = [{"role": "user", "content": prompt}]
        if system:
            messages.insert(0, {"role": "system", "content": system})
        return await self.chat(messages, max_tokens=max_tokens, temperature=temperature)

    async def chat(
        self,
        messages: list,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Multi-turn completion, walking the provider chain on failure."""
        self.initialize()
        while True:
            name = self.provider
            if name is None:
                return ""
            try:
                if name == "anthropic":
                    return await self._chat_anthropic(messages, max_tokens)
                if name == "openai":
                    return await self._chat_openai(messages, max_tokens, temperature)
                return await self._chat_ollama(messages, max_tokens, temperature)
            except Exception as e:
                # Ollama failures are almost always "server not running", which
                # retrying cannot fix either.
                if self._is_permanent(e) or name == "ollama":
                    self._retire(name, e)
                    continue  # try the next provider in the chain
                raise

    # ── providers ────────────────────────────────────────────────────────

    @staticmethod
    def _split_system(messages: list) -> tuple:
        """Anthropic takes the system prompt as its own argument, not a message."""
        system = " ".join(m["content"] for m in messages if m.get("role") == "system")
        turns = [m for m in messages if m.get("role") != "system"]
        return system, turns or [{"role": "user", "content": ""}]

    async def _chat_anthropic(self, messages: list, max_tokens: int) -> str:
        # temperature is deliberately omitted: sampling parameters are rejected
        # (400) on current Claude models.
        system, turns = self._split_system(messages)
        kwargs = {
            "model": settings.ANTHROPIC_MODEL,
            "max_tokens": max_tokens,
            "messages": turns,
        }
        if system:
            kwargs["system"] = system
        response = await self._anthropic.messages.create(**kwargs)
        return "".join(b.text for b in response.content if b.type == "text")

    async def _chat_openai(self, messages: list, max_tokens: int, temperature: float) -> str:
        response = await self._openai.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def _chat_ollama(self, messages: list, max_tokens: int, temperature: float) -> str:
        """Call a locally running Ollama server (free, no API key)."""
        url = settings.OLLAMA_BASE_URL.rstrip("/") + "/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            # Without this Ollama unloads the model after 5 min and every
            # later message pays a multi-minute reload from disk on CPU.
            "keep_alive": "30m",
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        # Local models on CPU are slow, so allow a generous ceiling.
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        return (data.get("message") or {}).get("content", "")

    async def health(self) -> dict:
        """Provider status, for diagnostics and the Settings screen."""
        self.initialize()
        ollama_models: List[str] = []
        ollama_up = False
        if "ollama" in self._chain:
            try:
                url = settings.OLLAMA_BASE_URL.rstrip("/") + "/api/tags"
                async with httpx.AsyncClient(timeout=3) as client:
                    r = await client.get(url)
                    r.raise_for_status()
                    ollama_models = [m["name"] for m in r.json().get("models", [])]
                    ollama_up = True
            except Exception:
                ollama_up = False
        return {
            "active_provider": self.provider,
            "chain": self._chain,
            "retired": sorted(self._dead),
            "ollama_running": ollama_up,
            "ollama_models": ollama_models,
            "ollama_model_configured": settings.OLLAMA_MODEL,
        }


llm_client = LLMClient()
