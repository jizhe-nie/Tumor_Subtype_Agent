import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from agent.skill_manager import load_all_skills


def get_tumor_agent_and_prompt():
    """
    [重构]：将 Agent 封装为工厂函数，供 Web UI 或 社交媒体 Bot 调用。
    返回初始化好的 agent 对象和系统提示词。
    """
    os.environ["OPENAI_API_KEY"] = "sk-d4887912a764401ca5565d20a4500fb6"
    os.environ["OPENAI_API_BASE"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    llm = ChatOpenAI(model="qwen-plus", temperature=0)

    # 动态加载所有技能
    tools = load_all_skills()
    tool_descriptions = "\n".join([f"- 【{t.name}】: {t.description}" for t in tools])

    # 动态系统提示词
    system_prompt_text = f"""你是一个顶级的生物信息学与计算生物学 AI 助手。
    你具备极强的自主逻辑推理和工作流规划能力。

    你当前已经动态挂载了以下极其强大的技能库：
    {tool_descriptions}

    【核心工作流法则】：
    1. 面对用户简短、模糊或不专业的指令（如“帮我分析这份数据”），你需要自己思考：需要调用哪些工具？逻辑顺序是什么？
    2. 如果用户没有提供足够的信息，请主动反问用户，索要必要信息。
    3. 如果用户要求编写新工具，请务必严格遵守：必须使用 `from langchain_core.tools import tool` 作为装饰器，确保包名和导入名正确，切勿产生幻觉。
    4. 你的最终目标是像资深研究员一样，交付有深度的生物学机制解读报告，而不是干巴巴的代码或中间数据。
    """

    agent = create_react_agent(llm, tools)
    return agent, SystemMessage(content=system_prompt_text)


# 如果直接运行此文件，给出提示（不再进入死循环）
if __name__ == "__main__":
    print("✅ 后端大脑已就绪！请运行 Web UI 或 社交媒体 Bot 来启动前端。")