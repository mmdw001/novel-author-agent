"""
工具系统 - 提供 LLM 可调用的各种工具
"""
import os
import json
import subprocess
import datetime
from typing import Dict, Any, List, Callable, Optional
from pathlib import Path


class Tool:
    """工具定义"""

    def __init__(self, name: str, description: str, parameters: Dict[str, Any],
                 handler: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def to_openai_schema(self) -> Dict:
        """转换为 OpenAI tools schema"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

    def execute(self, **kwargs) -> str:
        """执行工具并返回结果"""
        try:
            result = self.handler(**kwargs)
            return str(result)
        except Exception as e:
            return f"工具执行错误: {type(e).__name__}: {e}"


class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_defaults()

    def _register_defaults(self):
        """注册内置默认工具"""

        # 1. 执行 Python 代码
        self.register(Tool(
            name="execute_python",
            description="执行 Python 代码并返回结果。适合计算、数据分析等任务。",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要执行的 Python 代码"
                    }
                },
                "required": ["code"]
            },
            handler=lambda code: self._run_python(code)
        ))

        # 2. 读取文件
        self.register(Tool(
            name="read_file",
            description="读取文件内容。支持文本文件和代码文件。",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    }
                },
                "required": ["path"]
            },
            handler=lambda path: self._read_file(path)
        ))

        # 3. 写入文件
        self.register(Tool(
            name="write_file",
            description="写入内容到文件。会覆盖已有文件。",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容"
                    }
                },
                "required": ["path", "content"]
            },
            handler=lambda path, content: self._write_file(path, content)
        ))

        # 4. 列出目录
        self.register(Tool(
            name="list_directory",
            description="列出目录中的文件和子目录。",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "目录路径",
                        "default": "."
                    }
                },
                "required": []
            },
            handler=lambda path=".": self._list_dir(path)
        ))

        # 5. Shell 命令
        self.register(Tool(
            name="run_shell",
            description="在系统 Shell 中执行命令。注意：会实际执行命令。",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 shell 命令"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "超时时间(秒)",
                        "default": 30
                    }
                },
                "required": ["command"]
            },
            handler=lambda command, timeout=30: self._run_shell(command, timeout)
        ))

        # 6. 当前时间
        self.register(Tool(
            name="get_current_time",
            description="获取当前日期和时间信息。",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")
        ))

        # 7. 网络请求 (简单版)
        self.register(Tool(
            name="web_fetch",
            description="获取网页内容 (GET 请求)。",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要获取的 URL"
                    }
                },
                "required": ["url"]
            },
            handler=lambda url: self._web_fetch(url)
        ))

        # 8. 搜索记忆
        self.register(Tool(
            name="search_memory",
            description="在长期记忆中搜索相关信息。",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
            handler=lambda query, limit=5: self._search_memory_handler(query, limit)
        ))

        # 9. 保存记忆
        self.register(Tool(
            name="save_memory",
            description="保存一条重要信息到长期记忆。",
            parameters={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "要记住的内容"
                    },
                    "category": {
                        "type": "string",
                        "description": "分类标签",
                        "default": "general"
                    }
                },
                "required": ["content"]
            },
            handler=lambda content, category="general": self._save_memory_handler(content, category)
        ))

    def _search_memory_handler(self, query: str, limit: int = 5) -> str:
        """搜索记忆 - 需要外部注入"""
        if self.memory_system:
            return self.memory_system.search(query, limit)
        return "[记忆系统未启用]"

    def _save_memory_handler(self, content: str, category: str = "general") -> str:
        """保存记忆 - 需要外部注入"""
        if self.memory_system:
            self.memory_system.add(content, category)
            return f"已保存: {content[:50]}..."
        return "[记忆系统未启用]"

    # 内存系统引用 (由 Agent 注入)
    memory_system = None

    def register(self, tool: Tool):
        """注册工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    def get_schemas(self) -> List[Dict]:
        """获取所有工具的 OpenAI schema 列表"""
        return [t.to_openai_schema() for t in self._tools.values()]

    def execute(self, name: str, **kwargs) -> str:
        """执行工具"""
        tool = self.get(name)
        if not tool:
            return f"未知工具: {name}"
        return tool.execute(**kwargs)

    @staticmethod
    def _run_python(code: str) -> str:
        """安全执行 Python 代码"""
        try:
            # 使用 exec 并捕获输出
            local_vars = {}
            exec_globals = {"__builtins__": __builtins__}
            exec(code, exec_globals, local_vars)
            if local_vars:
                # 尝试获取最后一个表达式的值
                last_key = list(local_vars.keys())[-1]
                return str(local_vars[last_key])
            return "代码执行完成 (无返回值)"
        except Exception as e:
            return f"执行错误: {e}"

    @staticmethod
    def _read_file(path: str) -> str:
        """读取文件"""
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"文件不存在: {path}"
        try:
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            return f"[二进制文件无法直接读取] {path}"
        except Exception as e:
            return f"读取错误: {e}"

    @staticmethod
    def _write_file(path: str, content: str) -> str:
        """写入文件"""
        try:
            p = Path(path).expanduser().resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            return f"已成功写入 {len(content)} 字符到 {path}"
        except Exception as e:
            return f"写入错误: {e}"

    @staticmethod
    def _list_dir(path: str = ".") -> str:
        """列出目录"""
        try:
            p = Path(path).expanduser().resolve()
            if not p.exists():
                return f"目录不存在: {path}"
            items = []
            for item in p.iterdir():
                prefix = "📁" if item.is_dir() else "📄"
                items.append(f"{prefix} {item.name}")
            return "\n".join(items) if items else "(空目录)"
        except Exception as e:
            return f"列出错误: {e}"

    @staticmethod
    def _run_shell(command: str, timeout: int = 30) -> str:
        """执行 shell 命令"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[退出码: {result.returncode}]"
            return output.strip() or "(无输出)"
        except subprocess.TimeoutExpired:
            return f"命令超时 (>{timeout}s)"
        except Exception as e:
            return f"执行错误: {e}"

    @staticmethod
    def _web_fetch(url: str) -> str:
        """获取网页内容"""
        try:
            import requests
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            return resp.text[:5000] + ("..." if len(resp.text) > 5000 else "")
        except Exception as e:
            return f"请求错误: {e}"
