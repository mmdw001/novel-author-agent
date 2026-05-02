"""
Anthropic 模型适配器
"""
from typing import List, Optional, Dict, Any, Generator
from anthropic import Anthropic
from .base import BaseModelAdapter, Message, ToolCall, ModelResponse


class AnthropicAdapter(BaseModelAdapter):
    """Anthropic Claude API 适配器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = config.get("api_key", "") or ""
        api_base = config.get("api_base", "https://api.anthropic.com")
        self.client = Anthropic(api_key=api_key) if api_key else None

    def _get_model_name(self) -> str:
        return self.config.get("model_name") or self.config.get("model", {}).get("model_name", "claude-3-5-sonnet-20241022")

    def _get_max_tokens(self) -> int:
        return self.config.get("max_tokens") or self.config.get("model", {}).get("max_tokens", 4096)

    def _to_anthropic_messages(self, messages: List[Message]) -> List[Dict]:
        result = []
        system_content = None
        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
                continue
            d = {"role": "user" if msg.role == "user" else "assistant", "content": msg.content}
            result.append(d)
        return result, system_content

    def chat(self, messages: List[Message], tools: Optional[List[Dict]] = None,
             stream: bool = False) -> ModelResponse:
        if not self.client:
            return ModelResponse(content="[Anthropic API key 未配置]")

        anthropic_messages, system = self._to_anthropic_messages(messages)
        model = self._get_model_name()

        kwargs = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": self._get_max_tokens(),
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        response = self.client.messages.create(**kwargs)

        content = ""
        tool_calls = None
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input if isinstance(block.input, dict) else str(block.input),
                ))

        return ModelResponse(
            content=content,
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                "completion_tokens": response.usage.output_tokens if response.usage else 0,
            } if response.usage else None,
        )

    def chat_stream(self, messages: List[Message], tools: Optional[List[Dict]] = None) -> Generator[str, None, None]:
        if not self.client:
            yield "[Anthropic API key 未配置]"
            return

        anthropic_messages, system = self._to_anthropic_messages(messages)
        kwargs = {
            "model": self._get_model_name(),
            "messages": anthropic_messages,
            "max_tokens": self._get_max_tokens(),
            "stream": True,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
