"""
记忆系统 - 持久化长期记忆，支持语义搜索
"""
import json
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from config import config


class SimpleMemory:
    """
    轻量级记忆系统 - 使用 JSON 文件存储 + 简单关键词搜索
    如需更高级的语义搜索，可以安装 chromadb + sentence-transformers
    """

    def __init__(self):
        self.memory_dir = Path(config.get("memory.memory_dir"))
        self.enabled = config.get("memory.enabled", True)
        self.memories: List[Dict[str, Any]] = []
        self._loaded = False

        if self.enabled:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            self._load()

    def _get_file_path(self) -> Path:
        return self.memory_dir / "memories.json"

    def _load(self):
        """从文件加载记忆"""
        file_path = self._get_file_path()
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
            except Exception:
                self.memories = []
        self._loaded = True

    def _save(self):
        """保存记忆到文件"""
        file_path = self._get_file_path()
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"记忆保存失败: {e}")

    def add(self, content: str, category: str = "general", source: str = "conversation") -> str:
        """添加一条记忆"""
        if not self.enabled:
            return "[记忆系统未启用]"

        memory = {
            "id": str(uuid.uuid4())[:8],
            "content": content,
            "category": category,
            "source": source,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self.memories.append(memory)
        self._save()
        return memory["id"]

    def search(self, query: str, limit: int = 5) -> str:
        """搜索记忆 - 使用关键词匹配"""
        if not self.enabled or not self.memories:
            return "[暂无记忆]"

        query_lower = query.lower()
        keywords = query_lower.split()

        scored = []
        for mem in self.memories:
            content_lower = mem["content"].lower()
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scored.append((score, mem))

        # 按相关度排序
        scored.sort(key=lambda x: x[0], reverse=True)
        results = scored[:limit]

        if not results:
            return "[未找到相关记忆]"

        output = []
        for score, mem in results:
            ts = mem.get("timestamp", "")[:19]
            cat = mem.get("category", "general")
            content = mem["content"][:200]
            output.append(f"[{cat}] ({ts}) {content}")

        return "\n---\n".join(output)

    def get_recent(self, count: int = 5) -> List[Dict]:
        """获取最近的记忆"""
        return self.memories[-count:]

    def get_by_category(self, category: str) -> List[Dict]:
        """按分类获取记忆"""
        return [m for m in self.memories if m.get("category") == category]

    def clear(self):
        """清空记忆"""
        self.memories = []
        self._save()

    def get_stats(self) -> Dict:
        """获取记忆统计"""
        categories = {}
        for m in self.memories:
            cat = m.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total": len(self.memories),
            "categories": categories,
        }


class UserProfile:
    """用户画像 - 基于对话积累的用户信息"""

    def __init__(self):
        self.profile_path = config.data_dir / "profile.json"
        self.data: Dict[str, Any] = {"name": "", "preferences": {}, "facts": [], "interactions": 0}
        self._load()

    def _load(self):
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass

    def _save(self):
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def update(self, key: str, value: Any):
        self.data[key] = value
        self.data["interactions"] = self.data.get("interactions", 0) + 1
        self._save()

    def add_fact(self, fact: str):
        if fact not in self.data.get("facts", []):
            self.data.setdefault("facts", []).append(fact)
            self._save()

    def get_summary(self) -> str:
        """获取用户画像摘要"""
        parts = []
        if self.data.get("name"):
            parts.append(f"用户名称: {self.data['name']}")
        if self.data.get("facts"):
            parts.append("已知信息:\n" + "\n".join(f"- {f}" for f in self.data["facts"][-10:]))
        if self.data.get("preferences"):
            prefs = self.data["preferences"]
            parts.append(f"偏好: {json.dumps(prefs, ensure_ascii=False)}")
        return "\n".join(parts) if parts else "暂无用户画像信息"
