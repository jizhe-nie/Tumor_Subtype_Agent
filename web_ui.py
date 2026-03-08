import streamlit as st
import uuid
from langchain_core.messages import HumanMessage
from agent.tumor_agent import get_tumor_agent_and_prompt

st.set_page_config(page_title="OpenClaw 生信中枢", page_icon="🧬", layout="wide")

# 1. 初始化复杂的历史会话字典
if "chats" not in st.session_state:
    st.session_state.chats = {}  # 存储所有对话记录
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None


def create_new_chat():
    """创建一个全新的对话主题"""
    chat_id = str(uuid.uuid4())[:8]  # 生成短 ID
    agent, sys_prompt = get_tumor_agent_and_prompt()
    st.session_state.chats[chat_id] = {
        "title": f"新分析主题 {chat_id}",
        "agent": agent,
        "agent_messages": [sys_prompt],
        "ui_messages": [{"role": "assistant", "content": "您好！请问需要分析什么数据？"}]
    }
    st.session_state.current_chat_id = chat_id


# 如果刚启动，默认创建一个对话
if not st.session_state.chats:
    create_new_chat()

# 2. 侧边栏：多对话管理 UI
with st.sidebar:
    st.title("📂 对话主题管理")
    if st.button("➕ 新建生信分析", use_container_width=True):
        create_new_chat()

    st.divider()

    # 渲染当前所有的对话列表
    chat_ids_to_delete = []
    for chat_id, chat_data in st.session_state.chats.items():
        col1, col2 = st.columns([4, 1])
        with col1:
            # 切换对话按钮
            if st.button(chat_data["title"], key=f"btn_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
        with col2:
            # 删除对话按钮
            if st.button("🗑️", key=f"del_{chat_id}"):
                chat_ids_to_delete.append(chat_id)

    # 处理删除逻辑
    for cid in chat_ids_to_delete:
        del st.session_state.chats[cid]
        if st.session_state.current_chat_id == cid:
            st.session_state.current_chat_id = list(st.session_state.chats.keys())[
                0] if st.session_state.chats else None
            if not st.session_state.current_chat_id:
                create_new_chat()
        st.rerun()

st.title(f"🧬 OpenClaw - {st.session_state.chats[st.session_state.current_chat_id]['title']}")

# 获取当前正在活动的对话上下文
current_chat = st.session_state.chats[st.session_state.current_chat_id]

# 3. 渲染主界面聊天记录
for msg in current_chat["ui_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 4. 接收输入与 Agent 推理
if prompt := st.chat_input("请输入生信分析指令 (支持长文本粘贴)..."):
    # 如果是第一句话，更新侧边栏标题
    if len(current_chat["ui_messages"]) == 1:
        current_chat["title"] = prompt[:10] + "..."
        st.rerun()  # 刷新侧边栏标题

    current_chat["ui_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    current_chat["agent_messages"].append(HumanMessage(content=prompt))

    with st.chat_message("assistant"):
        with st.spinner("Agent 正在高速思考与调用算法工具..."):
            try:
                result = current_chat["agent"].invoke({"messages": current_chat["agent_messages"]})
                current_chat["agent_messages"] = result["messages"]
                final_answer = current_chat["agent_messages"][-1].content

                st.markdown(final_answer)
                current_chat["ui_messages"].append({"role": "assistant", "content": final_answer})
            except Exception as e:
                st.error(f"❌ 运行异常: {str(e)}")