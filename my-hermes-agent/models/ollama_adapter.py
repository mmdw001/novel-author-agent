"""
Ollama 模型适配器 - 支持本地模型
"""
import json
from typing import List, Optional, Dict, Any, Generator
import httpx
from .base import BaseModelAdapter, Message, ToolCall, ModelResponse


class OllamaAdapter(BaseModelAdapter):
    """Ollama 本地模型适配器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base = config.get("api_base", "http://localhost:11434")
        self.model_name = config.get("model", "llama3")

    def _get_messages(self, messages: List[Message]) -> List[Dict]:
        result = []
        for msg in messages:
            d = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                d["tool_calls"] = [
                    {"type": "function", "function": {"name": tc.name, "arguments": tc.arguments}}
                    for tc in msg.tool_calls
                ]
            result.append(d)
        return result

    def chat(self, messages: List[Message], tools: Optional[List[Dict]] = None,
             stream: bool = False) -> ModelResponse:
        url = f"{self.api_base}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": self._get_messages(messages),
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(url, json=payload)
                data = resp.json()

            content = data.get("message", {}).get("content", "")
            tool_calls_data = data.get("message", {}).get("tool_calls")

            tool_calls = None
            if tool_calls_data:
                tool_calls = []
                for tc in tool_calls_data:
                    fn = tc.get("function", {})
                    tool_calls.append(ToolCall(
                        id=tc.get("id", "") or f"tool_{hash(str(fn)) % 10000}",
                        name=fn.get("name", ""),
                        arguments=fn.get("arguments", {}),
                    ))

            return ModelResponse(
                content=content,
                tool_calls=tool_calls,
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                },
            )
        except Exception as e:
            return ModelResponse(content=f"[Ollama 连接错误: {e}]")

    def chat_stream(self, messages: List[Message], tools: Optional[List[Dict]] = None) -> Generator[str, None, None]:
        url = f"{self.api_base}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": self._get_messages(messages),
            "stream": True,
        }
        if tools:
            payload["tools"] = tools

        try:
            with httpx.Client(timeout=120.0) as client:
                with client.stream("POST", url, json=payload) as resp:
                    for line in resp.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                content = data.get("message", {}).get("content", "")
                                if content:
                                    yield content
                                if data.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            yield f"[Ollama 连接错误: {e}]"
