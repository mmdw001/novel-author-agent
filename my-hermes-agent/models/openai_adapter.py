"""
OpenAI 模型适配器
"""
from typing import List, Optional, Dict, Any, Generator
from openai import OpenAI
from .base import BaseModelAdapter, Message, ToolCall, ModelResponse


class OpenAIAdapter(BaseModelAdapter):
    """OpenAI API 适配器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = config.get("api_key", "") or config.get("model", {}).get("api_key", "")
        api_base = config.get("api_base", "") or config.get("model", {}).get("api_base", "")
        client_kwargs = {"api_key": api_key or "sk-placeholder"}
        if api_base:
            client_kwargs["base_url"] = api_base
        self.client = OpenAI(**client_kwargs)

    def _get_model_name(self) -> str:
        return self.config.get("model_name") or self.config.get("model", {}).get("model_name", "gpt-4o-mini")

    def _get_temperature(self) -> float:
        return self.config.get("temperature") or self.config.get("model", {}).get("temperature", 0.7)

    def _get_max_tokens(self) -> int:
        return self.config.get("max_tokens") or self.config.get("model", {}).get("max_tokens", 4096)

    def _to_openai_messages(self, messages: List[Message]) -> List[Dict]:
        result = []
        for msg in messages:
            d = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                d["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": str(tc.arguments)}
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                d["tool_call_id"] = msg.tool_call_id
            if msg.name:
                d["name"] = msg.name
            result.append(d)
        return result

    def _parse_response(self, response) -> ModelResponse:
        msg = response.choices[0].message
        tool_calls = None
        if msg.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=tc.function.arguments
                )
                for tc in msg.tool_calls
            ]
        return ModelResponse(
            content=msg.content or "",
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            } if response.usage else None,
            finish_reason=response.choices[0].finish_reason,
        )

    def chat(self, messages: List[Message], tools: Optional[List[Dict]] = None,
             stream: bool = False) -> ModelResponse:
        kwargs = {
            "model": self._get_model_name(),
            "messages": self._to_openai_messages(messages),
            "temperature": self._get_temperature(),
            "max_tokens": self._get_max_tokens(),
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        if stream:
            response = self.client.chat.completions.create(**kwargs, stream=True)
            content = ""
            tool_calls_map = {}
            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue
                if delta.content:
                    content += delta.content
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_map:
                            tool_calls_map[idx] = {
                                "id": tc.id or "",
                                "name": tc.function.name or "" if tc.function else "",
                                "arguments": "",
                            }
                        if tc.function and tc.function.arguments:
                            tool_calls_map[idx]["arguments"] += tc.function.arguments
                        if tc.id:
                            tool_calls_map[idx]["id"] = tc.id

            tool_calls = None
            if tool_calls_map:
                tool_calls = [
                    ToolCall(
                        id=tc["id"],
                        name=tc["name"],
                        arguments=tc["arguments"]
                    )
                    for tc in tool_calls_map.values()
                ]

            return ModelResponse(
                content=content,
                tool_calls=tool_calls,
            )

        response = self.client.chat.completions.create(**kwargs)
        return self._parse_response(response)

    def chat_stream(self, messages: List[Message], tools: Optional[List[Dict]] = None) -> Generator[str, None, None]:
        kwargs = {
            "model": self._get_model_name(),
            "messages": self._to_openai_messages(messages),
            "temperature": self._get_temperature(),
            "max_tokens": self._get_max_tokens(),
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content
