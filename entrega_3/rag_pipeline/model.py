"""Adaptador mínimo del SDK ya usado por el proyecto a un ChatModel LCEL."""
from typing import Any

from google import genai
from google.genai import types
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class GeminiChat(BaseChatModel):
    model: str = "gemini-3.1-flash-lite"
    temperature: float = 0.0

    @property
    def _llm_type(self) -> str:
        return "google-genai-sdk"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model_name": self.model, "temperature": self.temperature}

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        system = "\n".join(str(m.content) for m in messages if isinstance(m, SystemMessage))
        contents = [types.Content(role="model" if m.type == "ai" else "user",
                                  parts=[types.Part(text=str(m.content))])
                    for m in messages if not isinstance(m, SystemMessage)]
        config = dict(system_instruction=system, temperature=self.temperature,
                      automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))
        if stop:
            config["stop_sequences"] = stop
        for key in ("response_json_schema", "response_mime_type"):
            if key in kwargs:
                config[key] = kwargs[key]
        with genai.Client() as client:
            response = client.models.generate_content(
                model=self.model, contents=contents, config=types.GenerateContentConfig(**config),
            )
        usage = response.usage_metadata
        counts = None
        if usage is not None:
            input_tokens = usage.prompt_token_count
            output_tokens = usage.candidates_token_count
            total_tokens = usage.total_token_count
            if all(value is not None for value in (input_tokens, output_tokens, total_tokens)):
                counts = {"input_tokens": input_tokens, "output_tokens": output_tokens,
                          "total_tokens": total_tokens}
        if not response.text:
            raise RuntimeError("Gemini no devolvió texto; revisar bloqueo o respuesta del proveedor.")
        message = AIMessage(content=response.text, usage_metadata=counts,
                            response_metadata={"model_name": self.model,
                                "provider_usage": usage.model_dump(mode="json") if usage else None})
        return ChatResult(generations=[ChatGeneration(message=message)])
