import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import uuid
import json
from langchain_core.messages import HumanMessage
from agent.tumor_agent import get_tumor_agent_and_prompt

st.set_page_config(page_title="OpenClaw 生信中枢", page_icon="🧬", layout="wide")

# ==================== 配置持久化 ====================
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_brain", "api_config.json")

def load_api_config():
    default_config = {
        "api_key": "", "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model_name": "qwen-plus", "provider": "阿里云 (Qwen)",
        "use_independent_coder": False, "coder_api_key": "", "coder_api_base": "", "coder_model_name": "", "coder_provider": "DeepSeek"
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                local_data = json.load(f); default_config.update(local_data)
        except: pass
    return default_config

def save_api_config(config_dict):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_dict, f)

# 初始化 Session
local_config = load_api_config()
for k, v in local_config.items():
    if k not in st.session_state: st.session_state[k] = v

if "chats" not in st.session_state: st.session_state.chats = {}
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None

def create_new_chat():
    chat_id = str(uuid.uuid4())[:8]
    graph, sys_prompt = get_tumor_agent_and_prompt()
    st.session_state.chats[chat_id] = {
        "title": f"新主题 {chat_id}", "agent": graph, "agent_messages": [sys_prompt],
        "ui_messages": [{"role": "assistant", "content": "您好！协作分析中枢已就绪。"}]
    }
    st.session_state.current_chat_id = chat_id

if not st.session_state.chats and st.session_state.api_key:
    create_new_chat()

# ==================== 侧边栏配置 ====================
model_providers = {
    "阿里云 (Qwen)": {"base": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    "DeepSeek": {"base": "https://api.deepseek.com", "model": "deepseek-coder"},
    "智谱 AI (GLM)": {"base": "https://open.bigmodel.cn/api/paas/v4/", "model": "glm-4"},
    "月之暗面 (Kimi)": {"base": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
    "OpenAI": {"base": "https://api.openai.com/v1", "model": "gpt-4o"},
    "自定义 (兼容 OpenAI)": {"base": "", "model": ""}
}

with st.sidebar:
    st.title("⚙️ 配置中心")
    p1 = st.selectbox("主控厂商", list(model_providers.keys()), index=0)
    b1 = st.text_input("Base URL", value=model_providers[p1]["base"] or st.session_state.api_base)
    m1 = st.text_input("模型名称", value=model_providers[p1]["model"] or st.session_state.model_name)
    k1 = st.text_input("API Key", type="password", value=st.session_state.api_key)
    
    st.divider()
    use_c = st.checkbox("启用独立 Coder", value=st.session_state.use_independent_coder)
    if use_c:
        p2 = st.selectbox("Coder 厂商", list(model_providers.keys()), index=1)
        k2 = st.text_input("Coder Key", type="password", value=st.session_state.coder_api_key)
    else: k2 = ""
    
    if st.button("💾 应用配置", use_container_width=True):
        st.session_state.api_key = k1
        save_api_config({"api_key": k1, "api_base": b1, "model_name": m1, "provider": p1, "use_independent_coder": use_c, "coder_api_key": k2})
        st.rerun()

    st.divider()
    st.subheader("📂 历史会话")
    if st.button("➕ 新对话", use_container_width=True): create_new_chat(); st.rerun()
    for cid, data in st.session_state.chats.items():
        if st.button(data["title"], key=f"chat_{cid}", use_container_width=True):
            st.session_state.current_chat_id = cid; st.rerun()

# ==================== 主界面 ====================
if not st.session_state.api_key: st.info("请先配置 API Key"); st.stop()
curr = st.session_state.chats[st.session_state.current_chat_id]
st.title(f"🧬 {curr['title']}")

for m in curr["ui_messages"]:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("输入指令..."):
    curr["ui_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    curr["agent_messages"].append(HumanMessage(content=prompt))

    with st.chat_message("assistant"):
        status = st.status("🧬 正在执行协作流程...", expanded=True)
        log_area = status.container()
        try:
            ans = ""
            for chunk in curr["agent"].stream({"messages": curr["agent_messages"]}):
                for node_name, state in chunk.items():
                    m = state["messages"][-1]
                    curr["agent_messages"].append(m)
                    if m.content:
                        name = "🧠 主控" if node_name == "lead" else "👨‍💻 程序员"
                        log_area.markdown(f"**{name}**: {m.content}")
                        if node_name == "lead" and not (hasattr(m, "tool_calls") and m.tool_calls):
                            ans = m.content
                    if hasattr(m, "tool_calls") and m.tool_calls:
                        for tc in m.tool_calls: log_area.info(f"🛠️ 调度工具: `{tc['name']}`")
            status.update(label="🎉 分析完成", state="complete", expanded=False)
            if ans: 
                st.markdown(ans)
                curr["ui_messages"].append({"role": "assistant", "content": ans})
        except Exception as e:
            status.update(label="❌ 异常", state="error"); st.error(str(e))