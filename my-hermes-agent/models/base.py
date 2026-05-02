"""
模型适配器基类 - 定义统一的 LLM 接口
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from abc import ABC, abstractmethod


@dataclass
class Message:
    """统一的消息格式"""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_calls: Optional[List["ToolCall"]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ModelResponse:
    """模型响应"""
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None


class BaseModelAdapter(ABC):
    """模型适配器基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def chat(self, messages: List[Message], tools: Optional[List[Dict]] = None,
             stream: bool = False) -> ModelResponse:
        """发送聊天请求"""
        pass

    @abstractmethod
    def chat_stream(self, messages: List[Message], tools: Optional[List[Dict]] = None):
        """流式聊天 - 生成器"""
        pass

    def _format_messages(self, messages: List[Message]) -> List[Dict]:
        """将统一消息格式转换为 API 格式"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                **({"tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": str(tc.arguments)}
                    } for tc in (msg.tool_calls or [])
                ]} if msg.tool_calls else {}),
                **({"tool_call_id": msg.tool_call_id} if msg.tool_call_id else {}),
                **({"name": msg.name} if msg.name else {}),
            }
            for msg in messages
        ]

    @staticmethod
    def create(provider: str, config: Dict[str, Any]) -> "BaseModelAdapter":
        """工厂方法创建适配器"""
        if provider == "openai":
            from .openai_adapter import OpenAIAdapter
            return OpenAIAdapter(config)
        elif provider == "anthropic":
            from .anthropic_adapter import AnthropicAdapter
            return AnthropicAdapter(config)
        elif provider in ("ollama", "local"):
            from .ollama_adapter import OllamaAdapter
            return OllamaAdapter(config)
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
