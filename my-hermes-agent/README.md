<picture>
  <source media="(prefers-color-scheme: dark)" srcset="">
  <img alt="My Hermes Agent" src="" width="100%">
</picture>

# 🐚 My Hermes Agent

一个自改进的 AI 代理系统 —— 受 [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) 启发，用 Python 实现的轻量版。

## ✨ 特性

| 特性 | 说明 |
|------|------|
| 🖥️ **CLI 终端界面** | 全功能终端 UI，多行编辑，命令历史，流式输出 |
| 🧠 **记忆系统** | 持久化记忆，跨会话回忆，用户画像 |
| 🔧 **技能系统** | 可动态创建和自改进的技能，基于 agentmemory |
| 🛠️ **工具系统** | 文件操作、代码执行、网络请求等内置工具 |
| 🤖 **多模型支持** | OpenAI, Anthropic, Ollama, 自定义端点 |
| 🔄 **多平台消息** | Telegram, Discord 网关支持 |
| ⏰ **定时任务** | 内置 Cron 调度器 |
| 📁 **上下文文件** | 项目上下文注入，塑造每次对话 |

## 🚀 快速安装

```bash
pip install -r requirements.txt
python main.py
```

## 使用

启动后：
```
my-hermes> /model openai:gpt-4        # 切换模型
my-hermes> /persona 助手               # 设置人格
my-hermes> /memory 查看记忆             # 查看记忆
my-hermes> /skill list                 # 列出技能
my-hermes> /new                        # 新对话
my-hermes> 你好，帮我写一个 Python 脚本  # 正常对话
```

## 项目结构

```
my-hermes-agent/
├── main.py              # 入口
├── cli.py               # CLI 界面
├── config.py            # 配置管理
├── agent.py             # 核心代理
├── memory.py            # 记忆系统
├── skills.py            # 技能系统
├── tools.py             # 工具系统
├── models/              # 模型适配器
│   ├── __init__.py
│   ├── base.py
│   ├── openai_adapter.py
│   ├── anthropic_adapter.py
│   └── ollama_adapter.py
├── gateway/             # 消息网关
│   ├── __init__.py
│   ├── base.py
│   ├── telegram.py
│   └── discord_bot.py
├── cron/                # 定时任务
│   ├── __init__.py
│   └── scheduler.py
└── requirements.txt     # 依赖
```

## 📜 许可证

MIT
