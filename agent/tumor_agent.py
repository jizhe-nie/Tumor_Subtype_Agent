import os
import sys

# 将项目根目录加入系统路径，以便能够导入 tools 文件夹的内容
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 🌟 引入我们刚写的“技能管理器”
from agent.skill_manager import load_all_skills


def run_tumor_agent(user_query: str):
    os.environ["OPENAI_API_KEY"] = "sk-d4887912a764401ca5565d20a4500fb6"
    os.environ["OPENAI_API_BASE"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    llm = ChatOpenAI(model="qwen-plus", temperature=0)

    # Agent 人设
    system_prompt = """你是一个顶级的生物信息学 AI 助手。
    你的任务是帮助科研人员发现肿瘤亚型。
    你拥有一个动态技能库。请根据用户的需求，自主选择最合适的技能（工具）组合。
    如果数据是高维的，请务必先降维再聚类。"""

    # 🌟 核心变化：像 OpenClaw 一样，动态加载所有技能！
    # 以后无论你往 tools 文件夹里加多少个算法，这里的代码都不用改了！
    tools = load_all_skills()

    agent = create_react_agent(llm, tools)

    print(f"👤 [User]: {user_query}")

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_query)
    ]

    result = agent.invoke({"messages": messages})
    return result["messages"][-1].content


if __name__ == "__main__":
    query = "请用你所有的技能，帮我把 '../data/dummy_tcga_expression.csv' 这个包含500个基因的数据，先降维，再分成 3 个亚型。"
    final_answer = run_tumor_agent(query)
    print("\n🤖 [Agent 最终回复]:\n", final_answer)