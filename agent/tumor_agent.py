import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from agent.skill_manager import load_all_skills
from agent.context_manager import build_agent_system_prompt


def get_tumor_agent_and_prompt(api_key: str = None, base_url: str = None, model_name: str = "qwen-plus"):
    """
    [重构]：动态接收 API 配置的 Agent 工厂函数
    """
    # 如果没有传入配置，给一个默认提示兜底（防止报错崩溃）
    if not api_key:
        api_key = "请在前端配置 API Key"
    if not base_url:
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 动态初始化大模型（所有兼容 OpenAI 格式的 API 都可以用 ChatOpenAI 调用）
    llm = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model_name,
        temperature=0
    )

    # 动态加载所有技能
    tools = load_all_skills()
    tool_descriptions = "\n".join([f"- 【{t.name}】: {t.description}" for t in tools])

    # 动态加载所有技能
    tools = load_all_skills()
    tool_descriptions = "\n".join([f"- 【{t.name}】: {t.description}" for t in tools])

    # 🚀 从 agent_brain 物理文件夹动态生成充满灵魂的系统提示词
    system_prompt_text = build_agent_system_prompt(tool_descriptions)

    agent = create_react_agent(llm, tools)
    return agent, SystemMessage(content=system_prompt_text)


    agent = create_react_agent(llm, tools)
    return agent, SystemMessage(content=system_prompt_text)


# 如果直接运行此文件，给出提示（不再进入死循环）
if __name__ == "__main__":
    print("✅ 后端大脑已就绪！请运行 Web UI 或 社交媒体 Bot 来启动前端。")