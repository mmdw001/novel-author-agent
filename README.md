# 📚 小说作者 Agent — Novel Author Agent

> **全栈 AI 写作助手** — 基于 LLM（GPT/Claude 等）辅助创作 500 万字长篇小说的完整 Web 应用。

[![Next.js](https://img.shields.io/badge/Next.js-14+-000000?logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Prisma](https://img.shields.io/badge/Prisma-5+-2D3748?logo=prisma)](https://www.prisma.io/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3+-06B6D4?logo=tailwindcss)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ✨ 功能概览

### 🎯 平台适配与小说初始化
- **平台档案库** — 内置 6 大平台预设（番茄小说/起点中文网/晋江文学城/飞卢/七猫/自定义）
- **5 步初始化向导** — 选平台 → 设字数 → AI 取书名 → AI 写简介 → AI 生大纲
- **字数智能计算** — 输入总字数自动算出卷数/章节数/预估 Token 成本
- **平台风格注入** — 写作时自动注入平台风格指南到 AI Prompt
- **内容红线检测** — 不同平台审核规则自动规避

### 🧠 五层记忆系统
| 层级 | 内容 | 作用 |
|------|------|------|
| **热记忆** | 最近 3-5 章全文 | 短时上下文，保持情节连贯 |
| **温记忆** | 当前弧线章节摘要 | 中层上下文，把握情节走向 |
| **故事圣经** | 角色档案/时间线/情节线/伏笔 | 长期知识库，保障一致性 |
| **世界书** | 关键词驱动的动态设定注入 | 参考 SillyTavern，按需注入 |
| **风格指南** | 写作风格/措辞规则 | 保持全书风格统一 |

### 📝 核心写作功能
- **AI 续写** — 给定上下文自动生成下一章
- **AI 扩写/润色** — 对已有内容进行扩展或精修
- **批量写作** — 5-10 章管道式批量生成
- **多分支续写** — 每次生成 2-3 个不同走向的选项
- **场景级规划** — 章节内的精细场景编排
- **章节状态管线** — planned→writing→draft→reviewing→revising→approved→locked

### 🎭 沉浸式写作
- **POV 角色扮演** — AI 深入扮演指定角色进行描写
- **知识边界管理** — 角色只知道自己该知道的信息
- **角色声音模仿** — 对话风格、思维方式保持一致

### 🔍 一致性保障
- 自动一致性检查（每 10 章触发）
- 伏笔追踪看板 + 情节线活跃度监控
- 风格一致性检查 + 修订对比 Diff
- **母题追踪器** — 主题/象征/意象跨章节追踪

### 📊 结构分析
- 角色出场频率统计 + 情节张力曲线
- 伏笔老化预警 + 自动世界书条目生成
- **写作模式切换**（草稿/润色/聚焦）

### 🎯 去AI味系统 (De-AI-fication)
- **4 层策略**：Prompt 反模板指令 → 生成参数动态调节 → AI味评分引擎 → 多样性后处理器
- **AI味检测**：生成后自动打分 0-100，高分段落自动重写
- **多样性增强**：句首不重复、段落强制错落、词汇多样性检查
- **好/坏例子对比注入** + 人类作者风格参考

### 🔧 高级功能
- 多模型支持（OpenAI / Anthropic / 自定义）
- Token 成本监控与预算控制（写作前即可看到预估成本）
- 修订工作流（批注/版本/章节状态管线）
- 层级摘要管道（场景→章节→弧线→卷）
- 作者提示词系统（默认 + 自定义 + 模板变量 + 编译器）
- 全文搜索（FTS5）+ 导出（TXT/PDF/EPUB/HTML）

---

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端框架** | Next.js 14+ (App Router) |
| **UI 组件** | Tailwind CSS + shadcn/ui |
| **编辑器** | Tiptap (ProseMirror) |
| **后端** | Next.js API Routes |
| **数据库** | Prisma + SQLite + FTS5 |
| **LLM 集成** | 适配器模式（OpenAI / Anthropic / 自定义） |
| **流式输出** | SSE (Server-Sent Events) |

---

## 🗂️ 项目结构

```
novel-author-agent/
├── prisma/                  # 数据库 schema 与迁移
│   └── schema.prisma
├── src/
│   ├── app/                 # Next.js App Router 页面
│   │   ├── (dashboard)/     # 仪表盘布局
│   │   ├── projects/        # 项目管理 + 小说初始化向导
│   │   ├── writing/         # 写作编辑器
│   │   ├── worldbook/       # 世界书管理
│   │   ├── characters/      # 角色管理 + 母题追踪
│   │   └── analysis/        # 结构分析 + 一致性检查
│   ├── components/          # 共享组件
│   │   ├── ui/              # shadcn/ui 组件
│   │   └── editor/          # 编辑器组件
│   ├── lib/
│   │   ├── llm/             # LLM 适配器层
│   │   │   ├── base.ts
│   │   │   ├── openai.ts
│   │   │   ├── anthropic.ts
│   │   │   └── factory.ts
│   │   ├── memory/          # 五层记忆系统
│   │   ├── worldbook/       # 世界书引擎
│   │   ├── prompt/          # Prompt 编译系统 + 去AI味
│   │   ├── platform/        # 平台档案库 + 初始化向导
│   │   ├── antismell/       # 去AI味检测引擎
│   │   └── consistency/     # 一致性检查引擎
│   └── types/               # TypeScript 类型定义
├── plans/
│   └── novel-author-agent-plan.md  # 完整架构规划文档(18章)
└── docs/                    # 文档
```

---

## 🚀 实施路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| 1 | 项目初始化与核心架构（Next.js/Prisma/LLM适配器） | ⏳ 待开始 |
| 2 | 🆕 平台适配与小说初始化向导（平台档案库/5步向导） | 📅 |
| 3 | 五层记忆系统 + 层级摘要管道 | 📅 |
| 4 | 世界书引擎（SillyTavern 风格） | 📅 |
| 5 | 核心写作功能（续写/扩写/润色） | 📅 |
| 6 | 场景规划与多分支续写 | 📅 |
| 7 | 批量写作管道（5-10章并发） | 📅 |
| 8 | 角色与情节管理 + 母题追踪器 | 📅 |
| 9 | 沉浸式写作系统（POV/知识边界） | 📅 |
| 10 | 作者提示词系统 + 去AI味系统 | 📅 |
| 11 | 一致性保障 | 📅 |
| 12 | 结构分析与世界书自动生成 | 📅 |
| 13 | 修订工作流与章节状态管线 | 📅 |
| 14 | 高级功能（含成本控制） | 📅 |
| 15 | 优化与部署 | 📅 |

> 详细规划见 [`plans/novel-author-agent-plan.md`](plans/novel-author-agent-plan.md)

---

## 📄 License

MIT
