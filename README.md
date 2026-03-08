# 肿瘤多组学全自动 AI 分析平台 (OpenClaw) 技术开发进程文档

## 1. 项目概述

**项目名称**：Tumor_Subtype_Agent (OpenClaw 生信中枢)

**核心目标**：打造一个具备自主规划能力、面向计算生物学领域的顶级工业级 AI Agent。打破代码壁垒，允许科研人员/临床医生通过自然语言交互，全自动完成从数据预处理、多组学联合聚类 (SNF)、差异表达分析 (DEG) 到临床靶点发现与实体报告生成的端到端生信流水线。

**主要技术栈**：

- 核心 AI 框架：LangChain, LangGraph (create_react_agent)
- 大语言模型：通义千问 (Qwen-plus，经由 DashScope 兼容 API)
- 前端与交互：Streamlit (构建多会话 Web UI)
- 数据科学与生信算法：pandas, numpy, scikit-learn, scipy (纯手工实现的 SNF 底层逻辑)

## 2. 已完成功能模块

- **动态系统提示词与大脑重构 (tumor_agent.py)**：剥离了死板的硬编码工作流，将 Agent 改造成后端 API 形式（工厂函数）。Agent 启动时自动读取挂载工具的 name 和 description，实现“自由意志”的 Plan-and-Execute 规划。
- **多主题 Web UI 交互界面 (web_ui.py)**：基于 Streamlit 打造。彻底解决终端的“换行符陷阱”；利用 st.session_state 实现多对话主题（Session）的创建、切换与历史隔离。
- **高阶多组学联合聚类工具 (snf_clustering_tool.py)**：绕过年久失修的官方库，使用纯 Numpy 手写了高斯核亲和矩阵与相似性网络融合 (SNF) 算法，彻底解决 Scikit-Learn 的版本断裂报错，并输出标准聚类标签。
- **差异表达分析挖掘 (deg_analysis_tool.py)**：接收 SNF 输出的标签，执行高维统计检验（T-test/ANOVA），寻找多组学亚型的 Top 标志基因，并能智能解释因数据不平衡导致的统计学空白。
- **实体 Markdown 报告生成器 (generate_report_tool.py)**：赋予 Agent 将临床解读内容固化为实体 Markdown 文件的能力，解决大模型“凭空伪造 PDF 路径”的幻觉问题。
- **造物主之锤 (create_new_skill_tool.py)**：具备动态将大模型生成的 Python 代码写入系统的基础能力（目前处于“高危禁用/需监督”状态）。

## 3. 代码结构与文件组织

```plaintext
Tumor_Subtype_Agent/
├── data/                       # [本地忽略] 原始输入数据 (如表达矩阵、甲基化矩阵)
├── output/                     # [本地忽略] 结果输出目录
│   ├── multi_omics_snf/        # 存放 SNF 融合输出的标签文件
│   └── Final_Reports/          # 存放 Agent 生成的最终 Markdown 实体报告
├── tools/                      # Agent 的动态武器库
│   ├── snf_clustering_tool.py  # SNF 多组学融合聚类核心算法 (无依赖版)
│   ├── deg_analysis_tool.py    # 差异表达基因挖掘
│   ├── generate_report_tool.py # 实体报告生成器
│   ├── create_new_skill_tool.py# 动态技能写入器
│   └── ... (其他单组学/预处理工具)
├── agent/
│   ├── tumor_agent.py          # 核心大脑：封装 get_tumor_agent_and_prompt 工厂函数
│   └── skill_manager.py        # 负责动态扫描并挂载 tools 目录下的所有技能
└── web_ui.py                   # 全新的 Streamlit 前端交互入口
```
## 4. 数据模型与数据流向设计
文件路由（File Routing）隔离：Agent 不在内存中维护超大矩阵，所有工具通过文件绝对路径进行上下文传递。

输入节点：多组学特征矩阵并存于 data/。

计算中枢：SNF 产出 snf_cluster_labels_k4.csv。

输出节点：DEG 根据 label 提取 Marker Genes；最终解读传入 generate_report_tool 落地为 .md。

## 5. API / 核心工具接口定义
snf_clustering_tool

输入: data_paths: List[str] (多组学 CSV 绝对路径列表), n_clusters: int (分类数)。

返回: 成功信息及生成的 labels_path 路径字符串。

deg_analysis_tool

输入: clean_data_path: str (高维表达数据), labels_path: str (聚类名单)。

返回: 包含显著标志基因的摘要字符串（Agent 根据此文本组织语言报告）。

generate_report_tool

输入: report_title: str, report_content_md: str (报告全文本)。

返回: 生成的 .md 文件绝对路径。

## 6. 环境配置与依赖
环境变量：需在系统或代码中配置 OPENAI_API_KEY 和 OPENAI_API_BASE (现使用 DashScope Qwen 模型)。

核心依赖库 (requirements.txt 需包含)：
```plaintext
Plaintext
langchain
langchain-openai
langgraph
streamlit
pandas
numpy
scikit-learn
scipy
```
## 7. 当前待办事项（TODO）
[ ] 高优：搭建 Agent 代码沙盒 (Sandbox)。拦截 skill_builder 的写入，必须先经过 subprocess 测试编译与虚拟运行，确保无 \n 语法错误且无幻觉库名后，才允许落盘。

[ ] 中优：接入社交媒体/IM 机器人 (WeChat/Telegram)。复用已剥离的 tumor_agent.py 大脑，编写对应的事件监听网关。

[ ] 中优：开发数据探勘工具 (data_profiler_tool)。让 Agent 具备“读表”能力，在面对模糊指令时主动获取数据的行数列数和表头信息，辅助推理。

[ ] 低优：Markdown 到 PDF 的自动化导出。探索更稳定的排版方案（当前建议用户使用浏览器打开 md 后 Ctrl+P 导出）。

## 8. 遇到的挑战与解决方案
黑框框的“换行符陷阱”导致指令截断：

问题：终端无法接受粘贴的长段文本（内含回车），导致 Agent 提前触发推理，误判用户意图。

解决：果断废弃终端交互，全面转向 Streamlit Web UI 开发，利用 st.chat_input 实现完善的多行长文本传输。

大模型的“极端讨好型人格”与幻觉 (Hallucination)：

问题：Agent 在没有报告生成工具时，伪造了虚假的 PDF 路径；且擅自写入了格式损坏的 align_multiomics_samples.py 和带有错误包名的 snf_clustering_v2.py。

解决：

进行物理“除虫”，手动删除 tools/ 目录下的幻觉内鬼文件。

为系统添加真正的 generate_report_tool 实体化其写文件能力。

调整 Prompt，明确禁止伪造路径。

官方库版本断裂导致崩溃：

问题：snfpy 库底层调用了已被 scikit-learn 1.2+ 废弃的参数 (force_all_finite)，导致聚类必然失败。

解决：卸载不可靠的第三方库，直接使用 numpy 和基础科学栈手写了高斯核亲和力计算与 SNF 迭代融合算法。

## 9. 下一步开发计划
优先解决代码生成体系的安全问题。设计一套**“写代码 -> 虚拟环境试运行 -> 收集报错 -> 提示大模型重写 (Reflect) -> 测试通过 -> 落盘”** 的完整 Agentic Auto-Coding 护栏，彻底解锁大模型的动态开发潜能。随后，基于当前成熟的后端 API，无缝对接企业微信/微信接口。

## 10. 其他重要决策与说明
前端彻底解耦决策：tumor_agent.py 不再维护任何 while True 循环或 UI 逻辑，单纯作为一个 (agent, prompt) 的工厂服务。这为后续将大脑接入任意渠道（网页、手机端、API）奠定了根本性的架构基础。

放弃直接生成 PDF：Python 库生成 PDF 常面临中文字体乱码、表格排版崩溃等噩梦级问题。改用 Markdown 交付，把最终排版渲染权交给浏览器，是成本最低且效果最好的工程权衡。