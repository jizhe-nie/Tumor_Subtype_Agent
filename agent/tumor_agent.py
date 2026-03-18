import os
import json
import streamlit as st
from typing import Annotated, Sequence, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from agent.context_manager import build_agent_system_prompt
from agent.skill_manager import load_all_skills

# 🌟 使用缓存，解决后台疯狂扫描硬盘的问题
@st.cache_resource
def get_cached_skills():
    return load_all_skills()

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]

def get_model_configs():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(root, "agent_brain", "api_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def call_lead_agent(state: AgentState):
    cfg = get_model_configs()
    llm = ChatOpenAI(api_key=cfg["api_key"], base_url=cfg["api_base"], model=cfg["model_name"], temperature=0)
    
    # 主控 Agent 绝不能拿到沙盒工具
    all_tools = get_cached_skills()
    main_tools = [t for t in all_tools if t.name != "sandbox_execution_tool"]
    llm_with_tools = llm.bind_tools(main_tools)
    
    tool_desc = "\n".join([f"- {t.name}: {t.description}" for t in main_tools])
    system_prompt = build_agent_system_prompt(tool_desc)
    
    # 强制让主控学会“派活”
    instructions = "\n【多智能体规则】：你是主控，不具备写代码能力。遇到任何代码、绘图任务，必须呼叫 '@Coder' 并详述需求。不要自己尝试猜测路径。"
    
    messages = [SystemMessage(content=system_prompt + instructions)] + state["messages"]
    return {"messages": [llm_with_tools.invoke(messages)]}

def router(state: AgentState):
    last_message = state["messages"][-1]
    # 检查工具调用
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    # 检查是否需要转向 Coder (主控提到 Coder 时)
    content = last_message.content.lower() if last_message.content else ""
    if "@coder" in content or "程序员" in content:
        return END # 让流结束，Lead 输出文字，然后下一轮通过工具触发 Coder
    return END

def get_tumor_agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("lead", call_lead_agent)
    workflow.add_node("tools", ToolNode(get_cached_skills()))
    workflow.set_entry_point("lead")
    workflow.add_edge("tools", "lead")
    workflow.add_conditional_edges("lead", router, {"tools": "tools", END: END})
    return workflow.compile()

def get_tumor_agent_and_prompt():
    graph = get_tumor_agent_graph()
    all_tools = get_cached_skills()
    tool_desc = "\n".join([f"- {t.name}: {t.description}" for t in all_tools if t.name != "sandbox_execution_tool"])
    sys_prompt = build_agent_system_prompt(tool_desc)
    return graph, SystemMessage(content=sys_prompt)