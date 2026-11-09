"""Gemini con declaraciones explícitas; LangGraph controla la ejecución de tools.

Referencia: https://googleapis.github.io/python-genai/#function-calling
disable=True desactiva la ejecución automática del SDK, no la predicción de calls.
Se conserva Content original, incluidas las thought signatures de Gemini 3.
"""

import json
from uuid import uuid4

from google import genai
from google.genai import types
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from .trazabilidad import tramo


class GeminiAgente:
    def __init__(self, model: str = "gemini-3.1-flash-lite"):
        self.model = model
        self.consumo = []
        self.ultimo_error = None

    def bind_tools(self, herramientas):
        self.declarations = [types.FunctionDeclaration(
            name=t.name, description=t.description,
            parameters_json_schema=t.args_schema.model_json_schema(),
        ) for t in herramientas]
        return self

    async def ainvoke(self, messages):
        with tramo("gemini.agente", "llm", modelo=self.model) as span:
            message = await self._generar(messages)
            span.tokens(message.response_metadata.get("usage_metadata"), self.model)
            span.seleccion(message.tool_calls)
            return message

    async def _generar(self, messages):
        system = "\n".join(m.content for m in messages if isinstance(m, SystemMessage))
        contents = []
        provider_ids = {}
        for message in messages:
            if isinstance(message, AIMessage):
                original = message.additional_kwargs.get("gemini_content")
                contents.append(types.Content.model_validate(original) if original is not None else
                                types.Content(role="model", parts=[types.Part(text=message.content)]))
                provider_ids.update(message.additional_kwargs.get("provider_ids", {}))
            elif isinstance(message, HumanMessage):
                contents.append(types.Content(role="user", parts=[types.Part(text=message.content)]))
            elif isinstance(message, ToolMessage):
                contents.append(types.Content(role="user", parts=[types.Part(
                    function_response=types.FunctionResponse(
                        name=message.name, id=provider_ids.get(message.tool_call_id),
                        response=json.loads(message.content),
                    ))]))
        config = types.GenerateContentConfig(
            system_instruction=system, temperature=0,
            tools=[types.Tool(function_declarations=self.declarations)],
            tool_config=types.ToolConfig(function_calling_config=types.FunctionCallingConfig(mode="AUTO")),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        try:
            async with genai.Client().aio as client:
                response = await client.models.generate_content(model=self.model, contents=contents, config=config)
        except Exception as error:
            self.ultimo_error = {"tipo": type(error).__name__, "codigo": getattr(error, "code", None)}
            raise
        usage = response.usage_metadata
        self.consumo.append({"entrada": usage.prompt_token_count if usage else None,
                             "salida": usage.candidates_token_count if usage else None,
                             "total": usage.total_token_count if usage else None})
        if not response.candidates or not response.candidates[0].content:
            raise RuntimeError("Respuesta vacía del modelo")
        content = response.candidates[0].content
        calls, ids, text = [], {}, []
        for part in content.parts or []:
            if part.function_call:
                call = part.function_call
                local_id = call.id or str(uuid4())
                ids[local_id] = call.id
                calls.append({"name": call.name, "args": dict(call.args or {}), "id": local_id})
            elif part.text and not part.thought:
                text.append(part.text)
        counts = {key: value for key, value in {
            "input_tokens": usage.prompt_token_count if usage else None,
            "output_tokens": usage.candidates_token_count if usage else None,
            "total_tokens": usage.total_token_count if usage else None,
        }.items() if value is not None}
        return AIMessage(content="\n".join(text), tool_calls=calls,
                         response_metadata={"usage_metadata": counts, "model_name": self.model},
                         usage_metadata=counts if len(counts) == 3 else None,
                         additional_kwargs={"gemini_content": content.model_dump(mode="python", exclude_none=True),
                                            "provider_ids": ids})
