"""
CLI 界面 - 美观的终端交互界面
"""
import os
import sys
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings

from config import config
from agent import Agent


console = Console()


class CLI:
    """Hermes Agent CLI 界面"""

    BANNER = """
╔══════════════════════════════════════════════╗
║     🐚  My Hermes Agent v1.0                ║
║     自改进 AI 代理系统                       ║
╚══════════════════════════════════════════════╝
    """

    def __init__(self):
        self.agent = Agent()
        self.history_file = config.get("cli.history_file", "~/.hermes/history")

        # 确保历史目录存在
        os.makedirs(os.path.expanduser(os.path.dirname(self.history_file)), exist_ok=True)

        # 创建 prompt session
        kb = KeyBindings()

        @kb.add("c-c")
        def _(event):
            event.app.exit()

        self.session = PromptSession(
            history=FileHistory(os.path.expanduser(self.history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            key_bindings=kb,
        )

    def print_banner(self):
        """打印启动横幅"""
        console.print(Text(self.BANNER, style="bold cyan"))
        console.print(Panel(
            f"🤖 模型: [bold green]{config.get('model.provider')}:{config.get('model.model_name')}[/bold green]\n"
            f"🧠 记忆: [bold]{'✅ 已启用' if config.get('memory.enabled') else '❌ 已禁用'}[/bold] | "
            f"🔧 技能: [bold]{'✅ 已启用' if config.get('skills.enabled') else '❌ 已禁用'}[/bold] | "
            f"🛠️  工具: [bold]{len(self.agent.tools.list_tools())} 个[/bold]\n"
            f"💡 输入 [bold]/help[/bold] 查看命令列表",
            title="系统状态",
            border_style="blue",
        ))

    def handle_slash_command(self, cmd: str) -> Optional[bool]:
        """处理斜杠命令"""
        parts = cmd.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command in ("/help", "/h", "/?"):
            self.show_help()
            return True

        elif command in ("/quit", "/exit", "/q"):
            console.print("[yellow]再见！👋[/yellow]")
            sys.exit(0)

        elif command in ("/new", "/reset", "/clear"):
            self.agent.reset_conversation()
            console.print("[green]✅ 对话已重置[/green]")
            return True

        elif command == "/model":
            if not args:
                console.print(f"[cyan]当前模型: {config.get('model.provider')}:{config.get('model.model_name')}[/cyan]")
                console.print("使用: /model <provider>[:<model_name>]")
                console.print("例如: /model openai:gpt-4, /model anthropic, /model ollama:llama3")
                return True
            if ":" in args:
                provider, model_name = args.split(":", 1)
            else:
                provider = args
                model_name = None
            result = self.agent.change_model(provider, model_name)
            console.print(f"[green]✅ {result}[/green]")
            return True

        elif command == "/persona":
            if not args:
                current = config.get("session.persona")
                console.print(f"[cyan]当前人格: {current}[/cyan]")
                console.print("使用: /persona <描述>")
                return True
            config.set("session.persona", args)
            self.agent.system_prompt = self.agent._build_system_prompt()
            config.save()
            console.print(f"[green]✅ 人格已设置为: {args}[/green]")
            return True

        elif command in ("/memory", "/mem"):
            if args == "stats" or not args:
                stats = self.agent.memory.get_stats()
                table = Table(title="记忆统计", box=box.ROUNDED)
                table.add_column("指标", style="cyan")
                table.add_column("数值", style="green")
                table.add_row("总记忆数", str(stats["total"]))
                for cat, count in stats.get("categories", {}).items():
                    table.add_row(f"分类: {cat}", str(count))
                console.print(table)
                return True
            elif args == "clear":
                self.agent.memory.clear()
                console.print("[green]✅ 记忆已清空[/green]")
                return True
            elif args.startswith("search "):
                query = args[7:]
                results = self.agent.memory.search(query)
                console.print(Panel(results, title=f"🔍 搜索: {query}"))
                return True
            else:
                # 显示最近的记忆
                recent = self.agent.memory.get_recent(10)
                if not recent:
                    console.print("[yellow]暂无记忆[/yellow]")
                else:
                    table = Table(title="最近记忆", box=box.ROUNDED)
                    table.add_column("时间", style="dim")
                    table.add_column("分类", style="cyan")
                    table.add_column("内容", style="green")
                    for m in reversed(recent):
                        table.add_row(
                            m.get("timestamp", "")[11:19],
                            m.get("category", "general"),
                            m["content"][:60] + ("..." if len(m["content"]) > 60 else ""),
                        )
                    console.print(table)
                return True

        elif command in ("/skill", "/skills"):
            if args == "list" or not args:
                skills = self.agent.skills.list()
                if not skills:
                    console.print("[yellow]暂无技能[/yellow]")
                else:
                    table = Table(title="技能列表", box=box.ROUNDED)
                    table.add_column("名称", style="cyan")
                    table.add_column("分类", style="blue")
                    table.add_column("描述", style="green")
                    table.add_column("使用/成功率", style="yellow")
                    for s in skills:
                        rate = f"{s.success_count}/{s.usage_count}" if s.usage_count > 0 else "0/0"
                        table.add_row(s.name, s.category, s.description[:40], rate)
                    console.print(table)
                return True
            elif args.startswith("show "):
                name = args[5:]
                skill = self.agent.skills.get(name)
                if skill:
                    console.print(Panel(
                        Syntax(skill.code, "python", theme="monokai"),
                        title=f"📋 {skill.name} (v{skill.version})",
                    ))
                else:
                    console.print(f"[red]技能 '{name}' 不存在[/red]")
                return True
            elif args.startswith("delete "):
                name = args[7:]
                if self.agent.skills.remove(name):
                    console.print(f"[green]✅ 技能 '{name}' 已删除[/green]")
                else:
                    console.print(f"[red]技能 '{name}' 不存在[/red]")
                return True

        elif command == "/tool":
            tools = self.agent.tools.list_tools()
            table = Table(title=f"可用工具 ({len(tools)} 个)", box=box.ROUNDED)
            table.add_column("工具名称", style="cyan")
            table.add_column("描述", style="green")
            for t in tools:
                tool = self.agent.tools.get(t)
                if tool:
                    table.add_row(t, tool.description[:60])
            console.print(table)
            return True

        elif command in ("/stats", "/status"):
            stats = self.agent.get_stats()
            table = Table(title="系统状态", box=box.ROUNDED)
            table.add_column("项目", style="cyan")
            table.add_column("数值", style="green")
            for key, value in stats.items():
                table.add_row(key, str(value))
            console.print(table)
            return True

        elif command == "/save":
            config.save()
            console.print("[green]✅ 配置已保存[/green]")
            return True

        elif command == "/context":
            if args:
                # 添加上下文文件
                files = args.split()
                config.set("context_files", files)
                self.agent.system_prompt = self.agent._build_system_prompt()
                console.print(f"[green]✅ 已添加上下文文件: {files}[/green]")
            else:
                current = config.get("context_files", [])
                console.print(f"[cyan]当前上下文文件: {current or '(无)'}[/cyan]")
            return True

        else:
            console.print(f"[red]未知命令: {command}[/red]")
            console.print("输入 [bold]/help[/bold] 查看命令列表")
            return True

    def show_help(self):
        """显示帮助信息"""
        help_table = Table(title="📖 Hermes Agent 命令指南", box=box.ROUNDED, border_style="cyan")
        help_table.add_column("命令", style="bold cyan", width=22)
        help_table.add_column("说明", style="green")

        help_table.add_row("/help, /h", "显示帮助信息")
        help_table.add_row("/quit, /exit", "退出程序")
        help_table.add_row("/new, /reset", "重置对话")
        help_table.add_row("/model [p:m]", "切换模型提供商/模型名")
        help_table.add_row("/persona [描述]", "设置 AI 人格")
        help_table.add_row("/memory, /mem", "查看/管理记忆")
        help_table.add_row("  /mem search <q>", "搜索记忆")
        help_table.add_row("  /mem stats", "记忆统计")
        help_table.add_row("  /mem clear", "清空记忆")
        help_table.add_row("/skill, /skills", "查看/管理技能")
        help_table.add_row("  /skills show <n>", "查看技能详情")
        help_table.add_row("  /skills delete <n>", "删除技能")
        help_table.add_row("/tool", "查看可用工具")
        help_table.add_row("/stats, /status", "查看系统状态")
        help_table.add_row("/save", "保存配置")
        help_table.add_row("/context [files]", "设置上下文文件")

        console.print(help_table)
        console.print()
        console.print(Panel(
            "💡 [bold]提示:[/bold] 直接输入任何问题或任务，AI 代理会自动\n"
            "   使用工具、检索记忆和调用技能来帮助你！\n"
            "   [dim]按 Ctrl+C 退出当前对话[/dim]",
            border_style="yellow",
        ))

    def run(self):
        """运行 CLI 主循环"""
        self.print_banner()

        while True:
            try:
                # 获取用户输入
                user_input = self.session.prompt(
                    HTML("<ansicyan><b> my-hermes> </b></ansicyan>"),
                    multiline=config.get("cli.multiline", False),
                )

                # 跳过空输入
                if not user_input.strip():
                    continue

                # 处理斜杠命令
                if user_input.strip().startswith("/"):
                    self.handle_slash_command(user_input.strip())
                    continue

                # 处理普通对话
                with console.status("[bold cyan]思考中...", spinner="dots"):
                    response = self.agent.chat(user_input)

                # 显示响应
                console.print()
                console.print(Panel(
                    Markdown(response),
                    title="🤖 Hermes Agent",
                    border_style="green",
                ))
                console.print()

            except KeyboardInterrupt:
                console.print("\n[yellow]输入 /quit 退出程序[/yellow]")
                continue
            except EOFError:
                console.print("\n[yellow]再见！👋[/yellow]")
                break
            except Exception as e:
                console.print(f"\n[red]❌ 错误: {type(e).__name__}: {e}[/red]")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
                continue
