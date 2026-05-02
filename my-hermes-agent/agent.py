"""
核心代理引擎 - Hermes Agent 的大脑
管理对话循环、工具调用、记忆检索和技能执行
"""
import json
from typing import List, Optional, Dict, Any, Generator
from datetime import datetime

from config import config
from models.base import Message, ToolCall, ModelResponse
from models import BaseModelAdapter
from memory import SimpleMemory, UserProfile
from skills import SkillRegistry
from tools import ToolRegistry


class Agent:
    """
    Hermes Agent 核心代理

    特性:
    - 工具调用 (Tool Calling)
    - 记忆系统 (Memory)
    - 技能系统 (Skills)
    - 用户画像 (User Profile)
    - 自改进学习循环
    - 多模型支持
    """

    def __init__(self):
        self.model_adapter: Optional[BaseModelAdapter] = None
        self.memory = SimpleMemory()
        self.profile = UserProfile()
        self.skills = SkillRegistry()
        self.tools = ToolRegistry()

        # 注入记忆系统到工具中（避免循环引用）
        self.tools.memory_system = self.memory

        # 会话消息历史
        self.messages: List[Message] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 初始化模型
        self._init_model()

        # 系统提示
        self.system_prompt = self._build_system_prompt()

    def _init_model(self):
        """初始化 LLM 模型适配器"""
        provider = config.get("model.provider", "openai")
        model_config = {
            **config.get("model", {}),
            "api_key": config.get("model.api_key", ""),
            "api_base": config.get("model.api_base", ""),
        }
        # 也读取专门的提供商配置
        if provider == "anthropic":
            model_config["api_key"] = config.get("anthropic.api_key", "")
            model_config["api_base"] = config.get("anthropic.api_base", "")
        elif provider == "ollama":
            model_config["api_base"] = config.get("ollama.api_base", "http://localhost:11434")
            model_config["model_name"] = config.get("ollama.model", "llama3")

        self.model_adapter = BaseModelAdapter.create(provider, model_config)

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        persona = config.get("session.persona", "有帮助的 AI 助手")

        prompt = f"""你是 {config.get("agent_name", "My Hermes Agent")}，一个自改进的 AI 代理系统。

## 你的身份
{persona}

## 能力
1. **工具调用**：你可以使用各种工具来完成任务（文件操作、代码执行、网络请求等）
2. **记忆系统**：你有长期记忆，可以记住用户的重要信息。使用 save_memory 工具存储，用 search_memory 检索
3. **技能系统**：你有一套可执行的技能，可以自动学习和改进
4. **上下文感知**：你会记住对话历史并保持连贯性

## 行为准则
- 始终用 {config.get("model.provider", "中文")} 回复用户
- 如果需要使用工具，先想清楚再用
- 观察工具执行结果，然后再决定下一步
- 如果遇到重要信息，使用 save_memory 记住
- 在回复中引用相关记忆来展示你的记忆力"""

        # 添加上下文文件内容
        context_files = config.get("context_files", [])
        if context_files:
            context_content = []
            for filepath in context_files:
                try:
                    from pathlib import Path
                    p = Path(filepath).expanduser()
                    if p.exists():
                        context_content.append(f"=== {filepath} ===\n{p.read_text(encoding='utf-8')[:2000]}")
                except Exception:
                    pass
            if context_content:
                prompt += "\n\n## 上下文文件\n" + "\n\n".join(context_content)

        return prompt

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.messages.append(Message(role="user", content=content))

    def add_system_message(self, content: str):
        """添加系统消息"""
        self.messages.append(Message(role="system", content=content))

    def _prepare_messages(self) -> List[Message]:
        """准备发送给模型的消息列表"""
        msgs = []

        # 系统提示
        msgs.append(Message(role="system", content=self.system_prompt))

        # 注入记忆上下文
        if self.memory.enabled:
            # 获取最近的记忆来增强上下文
            recent = self.memory.get_recent(3)
            if recent:
                memory_text = "## 相关记忆\n" + "\n".join(
                    f"- {m['content'][:100]}" for m in recent
                )
                msgs.append(Message(role="system", content=memory_text))

        # 注入技能信息
        skills_text = self.skills.to_llm_context()
        if skills_text and skills_text != "[暂无技能]":
            msgs.append(Message(role="system",
                                content=f"## 可用技能\n{skills_text}\n你可以根据需要调用这些技能。"))

        # 注入用户画像
        profile_text = self.profile.get_summary()
        if profile_text and "暂无" not in profile_text:
            msgs.append(Message(role="system", content=f"## 用户信息\n{profile_text}"))

        # 对话历史
        msgs.extend(self.messages)

        return msgs

    def _compress_if_needed(self):
        """如果消息太长，进行压缩"""
        threshold = config.get("session.compress_threshold", 4000)
        max_history = config.get("session.max_history", 100)

        total_chars = sum(len(m.content or "") for m in self.messages)
        if total_chars > threshold or len(self.messages) > max_history:
            # 保留系统消息和最近的对话
            self.messages = self.messages[-max_history:]

    def chat(self, user_input: str) -> str:
        """
        处理用户输入并返回响应
        """
        self.add_user_message(user_input)

        # 主循环：最多执行 5 轮工具调用
        max_tool_rounds = 5
        for round_idx in range(max_tool_rounds):
            # 准备消息
            prepared = self._prepare_messages()

            # 获取模型响应
            response = self.model_adapter.chat(
                prepared,
                tools=self.tools.get_schemas(),
                stream=False,
            )

            # 检查是否有工具调用
            if response.tool_calls:
                # 添加助手消息（含工具调用）
                self.messages.append(Message(
                    role="assistant",
                    content=response.content or "",
                    tool_calls=response.tool_calls,
                ))

                # 执行每个工具
                for tc in response.tool_calls:
                    # 解析参数
                    try:
                        if isinstance(tc.arguments, str):
                            args = json.loads(tc.arguments)
                        else:
                            args = tc.arguments
                    except json.JSONDecodeError:
                        args = {}

                    # 执行工具
                    result = self.tools.execute(tc.name, **args)

                    # 记录技能使用
                    if tc.name in self.skills.get_names():
                        self.skills.record_usage(tc.name, "错误" not in result)

                    # 添加工具结果消息
                    self.messages.append(Message(
                        role="tool",
                        content=result[:3000],  # 限制长度
                        tool_call_id=tc.id,
                        name=tc.name,
                    ))
            else:
                # 没有工具调用，这是最终回复
                self.messages.append(Message(
                    role="assistant",
                    content=response.content or ""
                ))

                # 压缩历史
                self._compress_if_needed()

                return response.content or ""

        # 超过最大工具轮次
        return "任务完成（达到最大工具调用轮次）"

    def chat_stream(self, user_input: str) -> Generator[str, None, None]:
        """
        流式处理用户输入
        """
        self.add_user_message(user_input)
        prepared = self._prepare_messages()

        for chunk in self.model_adapter.chat_stream(
            prepared,
            tools=self.tools.get_schemas(),
        ):
            yield chunk

    def change_model(self, provider: str, model_name: Optional[str] = None):
        """切换模型"""
        config.set("model.provider", provider)
        if model_name:
            config.set("model.model_name", model_name)
        self._init_model()
        return f"已切换到 {provider}:{model_name or config.get('model.model_name')}"

    def reset_conversation(self):
        """重置对话"""
        self.messages = []
        # 从对话中学习：提取重要信息存入记忆
        return "对话已重置"

    def get_stats(self) -> Dict:
        """获取代理状态统计"""
        return {
            "model": f"{config.get('model.provider')}:{config.get('model.model_name')}",
            "messages": len(self.messages),
            "memory": self.memory.get_stats(),
            "skills": self.skills.get_stats(),
            "tools": len(self.tools.list_tools()),
            "session": self.session_id,
        }
