import httpx
from langfuse.decorators import observe

class OllamaEmbedder:
    def __init__(self, base_url: str, model: str, dimensions: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dimensions = dimensions

    @observe(as_type="generation", name="ollama_embed")
    async def embed(self, text: str) -> list[float]:
        from langfuse.decorators import langfuse_context
        langfuse_context.update_current_observation(
            model=self.model,
            input=text
        )
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json={"model": self.model, "input": text},
            )
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings") or []
        if not embeddings:
            raise RuntimeError("Ollama no devolvio embeddings.")
        vector = embeddings[0]
        if len(vector) != self.dimensions:
            raise RuntimeError(
                f"Dimension inesperada para {self.model}: {len(vector)} != {self.dimensions}."
            )
        return vector
