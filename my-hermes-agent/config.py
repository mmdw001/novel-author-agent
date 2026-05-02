"""
配置管理模块 - 管理 Hermes Agent 的所有配置
"""
import os
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class Config:
    """全局配置管理器"""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_defaults()
        return cls._instance

    def _load_defaults(self):
        """加载默认配置"""
        self._config = {
            # 代理名称
            "agent_name": "My Hermes Agent",

            # 模型配置
            "model": {
                "provider": os.getenv("HERMES_MODEL_PROVIDER", "openai"),
                "model_name": os.getenv("HERMES_MODEL_NAME", "gpt-4o-mini"),
                "temperature": float(os.getenv("HERMES_TEMPERATURE", "0.7")),
                "max_tokens": int(os.getenv("HERMES_MAX_TOKENS", "4096")),
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "api_base": os.getenv("OPENAI_API_BASE", ""),
            },

            # Anthropic 配置
            "anthropic": {
                "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                "api_base": os.getenv("ANTHROPIC_API_BASE", "https://api.anthropic.com"),
            },

            # Ollama 配置
            "ollama": {
                "api_base": os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
                "model": os.getenv("OLLAMA_MODEL", "llama3"),
            },

            # 记忆系统配置
            "memory": {
                "enabled": True,
                "embedding_model": os.getenv("HERMES_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
                "memory_dir": str(Path.home() / ".hermes" / "memory"),
                "max_memories_per_query": int(os.getenv("HERMES_MAX_MEMORIES", "10")),
            },

            # 技能系统配置
            "skills": {
                "enabled": True,
                "skills_dir": str(Path.home() / ".hermes" / "skills"),
                "auto_improve": True,
            },

            # CLI 配置
            "cli": {
                "theme": os.getenv("HERMES_THEME", "dark"),
                "history_file": str(Path.home() / ".hermes" / "history"),
                "show_thinking": True,
                "multiline": True,
            },

            # 会话配置
            "session": {
                "compress_threshold": int(os.getenv("HERMES_COMPRESS_THRESHOLD", "4000")),
                "max_history": int(os.getenv("HERMES_MAX_HISTORY", "100")),
                "persona": os.getenv("HERMES_PERSONA", "有帮助的 AI 助手"),
            },

            # 上下文文件
            "context_files": [],

            # 数据目录
            "data_dir": str(Path.home() / ".hermes"),
        }
        # 尝试从配置文件加载
        self._load_from_file()

    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        return Path(self._config["data_dir"]) / "config.yaml"

    def _load_from_file(self):
        """从文件加载配置"""
        config_path = self._get_config_path()
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)
                if user_config:
                    self._deep_merge(self._config, user_config)
            except Exception:
                pass

    def _deep_merge(self, base: dict, override: dict):
        """深度合并字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def save(self):
        """保存配置到文件"""
        config_path = self._get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)

    def get(self, key_path: str, default=None):
        """获取配置值，支持点号路径
        config.get("model.provider") -> "openai"
        """
        keys = key_path.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default

    def set(self, key_path: str, value: Any):
        """设置配置值"""
        keys = key_path.split(".")
        target = self._config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value

    @property
    def data_dir(self) -> Path:
        return Path(self._config["data_dir"])

    def ensure_dirs(self):
        """确保所有需要的目录存在"""
        dirs = [
            self.data_dir,
            Path(self._config["memory"]["memory_dir"]),
            Path(self._config["skills"]["skills_dir"]),
            self.data_dir / "sessions",
            self.data_dir / "logs",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


# 全局单例
config = Config()
