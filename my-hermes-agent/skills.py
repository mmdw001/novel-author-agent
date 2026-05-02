"""
技能系统 - 可动态创建、存储和自改进的技能
"""
import json
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from config import config


class Skill:
    """单个技能定义"""

    def __init__(self, name: str, description: str, code: str,
                 category: str = "general", version: int = 1,
                 metadata: Optional[Dict] = None):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.description = description
        self.code = code
        self.category = category
        self.version = version
        self.metadata = metadata or {}
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = self.created_at
        self.usage_count = 0
        self.success_count = 0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "category": self.category,
            "version": self.version,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Skill":
        skill = cls(
            name=data["name"],
            description=data.get("description", ""),
            code=data.get("code", ""),
            category=data.get("category", "general"),
            version=data.get("version", 1),
            metadata=data.get("metadata", {}),
        )
        skill.id = data.get("id", skill.id)
        skill.created_at = data.get("created_at", skill.created_at)
        skill.updated_at = data.get("updated_at", skill.updated_at)
        skill.usage_count = data.get("usage_count", 0)
        skill.success_count = data.get("success_count", 0)
        return skill


class SkillRegistry:
    """
    技能注册中心 - 管理技能的 CRUD 和自改进
    Hermes Agent 的核心特性：技能可以从经验中自我改进
    """

    def __init__(self):
        self.skills_dir = Path(config.get("skills.skills_dir"))
        self.auto_improve = config.get("skills.auto_improve", True)
        self._skills: Dict[str, Skill] = {}
        self._loaded = False

        if config.get("skills.enabled", True):
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            self._load()

    def _get_file_path(self) -> Path:
        return self.skills_dir / "skills.json"

    def _load(self):
        """从文件加载技能"""
        file_path = self._get_file_path()
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    skill = Skill.from_dict(item)
                    self._skills[skill.name] = skill
            except Exception:
                pass

        # 如果没有技能，添加一些内置示例技能
        if not self._skills:
            self._add_builtin_skills()

        self._loaded = True

    def _save(self):
        """保存技能到文件"""
        file_path = self._get_file_path()
        try:
            data = [s.to_dict() for s in self._skills.values()]
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"技能保存失败: {e}")

    def _add_builtin_skills(self):
        """添加内置技能示例"""
        builtins = [
            Skill(
                name="文件分析",
                description="分析文件内容，提取关键信息，总结文档要点",
                code=(
                    "def execute(context: dict) -> str:\n"
                    '    """分析文件内容并总结"""\n'
                    "    file_content = context.get('content', '')\n"
                    "    if not file_content:\n"
                    "        return '没有提供文件内容'\n"
                    "    lines = file_content.split('\\n')\n"
                    "    word_count = len(file_content.split())\n"
                    '    return f"文件共 {len(lines)} 行, {word_count} 词"'
                ),
                category="analysis",
            ),
            Skill(
                name="代码审查",
                description="审查代码质量，发现潜在问题，提出改进建议",
                code=(
                    "def execute(context: dict) -> str:\n"
                    '    """审查代码质量"""\n'
                    "    code = context.get('code', '')\n"
                    "    if not code:\n"
                    "        return '没有提供代码'\n"
                    "    issues = []\n"
                    "    if len(code) > 1000:\n"
                    "        issues.append('代码过长，建议拆分为更小的函数')\n"
                    "    if 'TODO' in code:\n"
                    "        issues.append('包含 TODO 注释')\n"
                    "    if 'print(' in code:\n"
                    "        issues.append('包含 print 语句，建议使用日志')\n"
                    "    return '\\n'.join(issues) if issues else '代码质量良好'"
                ),
                category="development",
            ),
            Skill(
                name="对话总结",
                description="总结对话历史，提取关键决策和行动项",
                code=(
                    "def execute(context: dict) -> str:\n"
                    '    """总结对话内容"""\n'
                    "    messages = context.get('messages', [])\n"
                    "    if not messages:\n"
                    "        return '没有对话内容'\n"
                    '    summary = f"共 {len(messages)} 条消息\\n"\n'
                    "    return summary + '对话已记录'"
                ),
                category="communication",
            ),
        ]
        for skill in builtins:
            self._skills[skill.name] = skill
        self._save()

    def get(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self._skills.get(name)

    def add(self, skill: Skill):
        """添加新技能"""
        self._skills[skill.name] = skill
        self._save()

    def remove(self, name: str) -> bool:
        """删除技能"""
        if name in self._skills:
            del self._skills[name]
            self._save()
            return True
        return False

    def list(self, category: Optional[str] = None) -> List[Skill]:
        """列出技能"""
        if category:
            return [s for s in self._skills.values() if s.category == category]
        return list(self._skills.values())

    def get_names(self) -> List[str]:
        """获取所有技能名称"""
        return list(self._skills.keys())

    def record_usage(self, name: str, success: bool = True):
        """记录技能使用情况（用于自改进）"""
        skill = self._skills.get(name)
        if skill:
            skill.usage_count += 1
            if success:
                skill.success_count += 1
            self._save()

    def get_stats(self) -> Dict:
        """获取技能统计"""
        categories = {}
        for s in self._skills.values():
            categories[s.category] = categories.get(s.category, 0) + 1
        total_usage = sum(s.usage_count for s in self._skills.values())
        return {
            "total": len(self._skills),
            "categories": categories,
            "total_usage": total_usage,
        }

    def to_llm_context(self) -> str:
        """将技能列表转换为 LLM 上下文文本"""
        if not self._skills:
            return "[暂无技能]"
        parts = []
        for s in self._skills.values():
            success_rate = (s.success_count / s.usage_count * 100) if s.usage_count > 0 else 100
            parts.append(
                f"- {s.name} (v{s.version}): {s.description} "
                f"[使用{s.usage_count}次, 成功率{success_rate:.0f}%]"
            )
        return "\n".join(parts)
