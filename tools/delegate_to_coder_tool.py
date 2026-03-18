import os
import sys
import json
from langchain_core.tools import tool

# 🌟 1. 物理定位根目录（这是解决所有路径问题的“定海神针”）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@tool
def delegate_to_coder_tool(task_description: str) -> str:
    """
    【多Agent协同入口】：呼叫底层的 '程序员 Agent' (Coder Agent)。
    当你需要进行数据清洗、统计分析、或写代码绘图时，必须调用此工具将任务外包。
    """
    # 🌟 2. 动态注入路径，确保内部 Agent 能识别 sandbox_execution_tool
    tools_dir = os.path.join(PROJECT_ROOT, "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import SystemMessage
    
    # 使用绝对路径导入沙盒工具，解决 "No module named"
    try:
        import sandbox_execution_tool
        sandbox_tool = sandbox_execution_tool.sandbox_execution_tool
    except Exception as e:
        return f"❌ 严重导入错误：无法加载沙盒模块。详情: {str(e)}"

    # 读取 API 配置
    config_path = os.path.join(PROJECT_ROOT, "agent_brain", "api_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    c_key = cfg.get("coder_api_key") or cfg.get("api_key")
    c_base = cfg.get("coder_api_base") or cfg.get("api_base")
    c_model = cfg.get("coder_model_name") or cfg.get("model_name")

    llm = ChatOpenAI(api_key=c_key, base_url=c_base, model=c_model, temperature=0)
    
    # 🌟 3. 在 Prompt 中强制注入绝对路径，解决 Coder 找不到数据的问题
    coder_instruction = f"""你是一个生信程序员。
    【项目根目录】：{PROJECT_ROOT}
    你的任务：{task_description}。
    
    【铁律】：
    1. 你必须使用 `sandbox_execution_tool` 来运行代码。
    2. 如果需要读取文件（如 ./data/xxx.csv），请务必在代码中拼接为绝对路径：
       `os.path.join(r"{PROJECT_ROOT}", "data", "xxx.csv")`。
    3. 保存图片也请保存到 `{PROJECT_ROOT}/output/` 目录下。
    4. 代码开头必须写 `import os, pandas, numpy`。
    """
    
    coder_agent = create_react_agent(llm, tools=[sandbox_tool])
    
    try:
        # 增加 recursion_limit 允许 Coder 自我纠错
        result = coder_agent.invoke({"messages": [("user", coder_instruction)]}, {"recursion_limit": 10})
        return f"✅ Coder 汇报执行结果：\n{result['messages'][-1].content}"
    except Exception as e:
        return f"❌ Coder 运行崩溃: {str(e)}"