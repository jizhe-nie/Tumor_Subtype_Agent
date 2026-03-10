# 肿瘤多组学全自动 AI 分析平台 (Tumor_Subtype_Agent) 技术开发进程文档

## 1. 项目概述

**项目名称**：Tumor_Subtype_Agent (基于外脑架构的多组学生信中枢)

**核心目标**：构建一个具备高度专业性、冷酷人格、且拥有长期记忆与自我进化能力的生信 AI Agent。系统不仅能全自动执行多组学融合聚类（SNF）与差异分析，还能根据外科医生的偏好生成高度定制化的实体报告，彻底消除大模型的“讨好型人格”与“失忆症”。

**主要技术栈**：
- 核心 AI 框架：LangChain, LangGraph (create_react_agent)
- 前端交互：Streamlit (支持流式进度直播与本地状态持久化)
- 记忆架构：基于文件系统的外脑架构（Out-of-core Memory），Text > Brain 理念。
- 生信算法库：pandas, numpy, scikit-learn

## 2. 已完成功能模块

- **多会话 Web UI 彻底修复**：解决了 Streamlit 生命周期陷阱导致的 st.rerun() 无限重启和吞字问题，实现了流畅的多对话主题管理。
- **多模型 API 动态配置与持久化**：在前端侧边栏新增模型“引擎舱”，支持动态切换国内外主流模型（Qwen, DeepSeek, GLM, Kimi, GPT-4o），并通过本地 api_config.json 实现配置的永久保存。
- **流式输出与“内心独白” (Streaming Monologue)**：重构了前端的渲染逻辑，使用 st.status 折叠框实时捕获并展示 Agent 的思考过程（💭 AI 思考）和工具调用状态，极大提升了用户等待体验。
- **“智能体外脑”物理架构 (agent_brain/)**：建立了独立的 Markdown 文件集，分别管控 Agent 的性格（SOUL.md）、操作规程（AGENTS.md）、历史经验（MEMORY.md）和用户画像（USER.md）。
- **上下文读取引擎 (context_manager.py)**：实现了 70/20 比例的安全截断算法，确保外脑文件内容被安全、完整地注入到大模型的 System Prompt 中。
- **Agent 自我进化工具 (update_agent_brain_tool.py)**：赋予 Agent 修改自身记忆的写权限。Agent 能够在分析中主动提炼价值信息，并以 Append 模式带时间戳地写入对应的大脑分区。

## 3. 代码结构与文件组织

```plaintext
Tumor_Subtype_Agent/
├── agent_brain/                # 🧠 [新增] 智能体外脑容器（持久化存储）
│   ├── api_config.json         # API 密钥与模型选择的本地缓存
│   ├── SOUL.md                 # 核心人格与价值观（如：冷酷、专业、反讨好）
│   ├── AGENTS.md               # 生信操作强制规程（如：K值铁律、必须画图）
│   ├── MEMORY.md               # 长期业务记忆与科学发现
│   └── USER.md                 # 用户身份与阅读偏好
├── tools/                      # 🛠️ 动态武器库
│   ├── update_agent_brain_tool.py # [新增] 记忆刻刀：用于更新外脑文件
│   ├── snf_clustering_tool.py  # SNF 多组学融合聚类
│   ├── generate_report_tool.py # 实体报告生成器
│   └── ... 
├── agent/
│   ├── tumor_agent.py          # 核心大脑入口：封装工厂函数
│   ├── context_manager.py      # [新增] 读取引擎：将外脑组装为 Prompt
│   └── skill_manager.py        # 动态扫描挂载工具
└── web_ui.py                   # 全新修复并支持流式直播的 Streamlit 前端
```

**关键函数说明**：`context_manager.py` 中的 `build_agent_system_prompt` 负责物理文件的读取与组装；`tumor_agent.py` 不再硬编码 Prompt，而是完全依赖 `context_manager` 提供的灵魂数据。

## 4. 数据模型与数据库设计

- **无关系型数据库**：本项目采用极简的 **文件系统即数据库 (File-system as DB)** 架构。
- **配置持久化**：`agent_brain/api_config.json` 采用 JSON 格式，包含 `api_key`, `api_base`, `model_name`, `provider` 字段。
- **记忆持久化**：`agent_brain/*.md` 文件。写入采用追加模式（append），格式统一为 `\n\n> [时间戳] 记忆追加:\n具体内容`。

## 5. API 接口定义

- 废弃了直接写死在 `os.environ` 的环境变量模式。
- `get_tumor_agent_and_prompt(api_key, base_url, model_name)` 函数现已实现参数化，全面兼容所有符合 OpenAI API 规范的提供商接口。

## 6. 环境配置与依赖

**核心依赖更新（requirements.txt）**：

```plaintext
langchain
langchain-openai
langgraph
streamlit
pandas
numpy
```

## 7. 当前待办事项（TODO）

- [ ] **高优**：搭建安全代码沙盒 (Sandbox)。为 `create_new_skill_tool` 加上基于子进程（subprocess）的预编译与黑盒测试，拦截语法错误，彻底解决 Agent 乱写代码导致系统崩溃的隐患。
- [ ] **中优**：开发数据探勘工具 (`data_profiler_tool`)。让 Agent 在分析前能通过专用工具“偷看”数据的行列数和表头，代替盲目猜测。
- [ ] **低优**：社交媒体网关。编写基于 Flask/FastAPI 的 Webhook，对接微信或企业微信机器人。

## 8. 遇到的挑战与解决方案

### Streamlit 输入框吞字与卡死
- **问题**：在 `st.chat_input` 触发的当回合内错误调用了 `st.rerun()`，导致程序在写入历史记录前就中断重启。
- **解决**：将 `st.rerun()` 逻辑后置到所有 Agent 推理和状态更新完成后进行。

### 跨语言调用 (R 语言) 导致进程死锁
- **问题**：Agent 擅自调用 `consensus_clustering_tool`（依赖 R 语言），因包缺失弹出隐藏的控制台确认框，导致后台永久卡死。
- **解决**：在 `AGENTS.md` 中写入“K值铁律”，强制限制 Agent 在未获授权时使用超长耗时算法。

### Agent 记忆查重失败与拒绝回答问题
- **问题**：在冷酷人设下，Agent 拒绝正面回答“我是谁”，且反复将相同偏好追加写入 `USER.md`。
- **解决**：在提示词底层加入了【正面回答原则】和【记忆查重与更新铁律】，要求其在调用写入工具前比对上下文，阻断重复写入。

## 9. 下一步开发计划

**终极目标**：解锁“代码沙盒”并释放 Agent 的绝对自由。
由于目前系统已具备完善的记忆和性格约束，下一步必须构建隔离的 Python 运行沙盒。沙盒建成后，我们将撕掉大部分生硬的“不准写代码”等限制性 Prompt，让 Agent 在沙盒内自由试错、编写脚本、自我进化，达成真正的 AGI 业务形态。

## 10. 其他重要决策与说明

- **全面拥抱“Text > Brain”哲学**：明确大模型的上下文窗口仅作为“短时工作台”，任何业务事实、用户偏好和规章制度必须落盘为 `.md` 实体文件。
- **反讨好型人格设计**：系统明确抵制“客服式”的无效废话。Agent 的首要任务是直接交付含有医学洞察的数据报告（如聚焦 FDA 靶向药、减少单纯统计学指标的堆砌），这使得系统更契合严肃临床和科研场景。