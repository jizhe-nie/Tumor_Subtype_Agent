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
    # 终极测试：下达五连招指令！
    query = """
    这是最新的 TCGA BRCA 原始数据 '../data/tcga_brca_expr.tsv'。
    请帮我走一遍极其严谨的科学发现流水线：
    1. 清洗数据。
    2. PCA 降维到 20 维。
    3. 调用【权威一致性聚类 (R语言版)】评估最优的 k 值。
    4. 获取到最优的 k 后，调用 K-Means 工具进行最终聚类。
    5. 调用【可视化工具】画出最终聚类散点图。
    处理完后，请告诉我 R 语言生成的图表和你的散点图分别存在哪里了，并做个精简的总结。
    """

    try:
        final_answer = run_tumor_agent(query)
        print("\n🤖 [Agent 最终回复]:\n", final_answer)
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
