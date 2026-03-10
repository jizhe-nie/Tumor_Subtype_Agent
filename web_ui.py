import streamlit as st
import uuid
import os
import json
from langchain_core.messages import HumanMessage, messages_from_dict, messages_to_dict
from agent.tumor_agent import get_tumor_agent_and_prompt

st.set_page_config(page_title="OpenClaw 生信中枢", page_icon="🧬", layout="wide")

# ==================== 本地配置持久化逻辑 ====================
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_brain", "api_config.json")
CHAT_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_brain", "chat_history.json")


def load_api_config():
    """从本地读取 API 配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"api_key": "", "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model_name": "qwen-plus",
            "provider": "阿里云 (Qwen)"}


def save_api_config(api_key, api_base, model_name, provider):
    """将 API 配置永久保存到本地"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"api_key": api_key, "api_base": api_base, "model_name": model_name, "provider": provider}, f)


# ==================== 对话历史持久化逻辑 ====================
def load_chat_history():
    """从本地读取对话历史"""
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"chats": {}, "current_chat_id": None}


def save_chat_history():
    """将对话历史永久保存到本地（不保存 agent 实例）"""
    os.makedirs(os.path.dirname(CHAT_HISTORY_FILE), exist_ok=True)
    data = {"chats": {}, "current_chat_id": st.session_state.current_chat_id}
    for chat_id, chat_data in st.session_state.chats.items():
        data["chats"][chat_id] = {
            "title": chat_data.get("title", f"新分析主题 {chat_id}"),
            "ui_messages": chat_data.get("ui_messages", []),
            "agent_messages": messages_to_dict(chat_data.get("agent_messages", [])),
        }
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def ensure_chat_agent(chat_data):
    """确保当前对话有可用 agent 与系统提示词"""
    if chat_data.get("agent") is None:
        agent, sys_prompt = get_tumor_agent_and_prompt(
            api_key=st.session_state.api_key,
            base_url=st.session_state.api_base,
            model_name=st.session_state.model_name
        )
        chat_data["agent"] = agent
        if not chat_data.get("agent_messages"):
            chat_data["agent_messages"] = [sys_prompt]
        else:
            try:
                first_msg = chat_data["agent_messages"][0]
                if getattr(first_msg, "type", "") != "system":
                    chat_data["agent_messages"].insert(0, sys_prompt)
            except Exception:
                chat_data["agent_messages"] = [sys_prompt] + chat_data.get("agent_messages", [])


def derive_title_from_ai(answer_text: str, max_len: int = 16) -> str:
    """基于 AI 对用户问题的理解生成主题标题（过滤系统提示类文本）"""
    if not answer_text:
        return ""
    blacklist = {
        "[系统载入完毕]",
        "系统载入完毕",
        "流程执行完毕",
        "流程执行完成",
        "执行完毕",
        "执行完成",
    }
    lines = [ln.strip() for ln in answer_text.strip().splitlines() if ln.strip()]
    for line in lines:
        clean = line.replace("*", "").replace("#", "").strip()
        if clean in blacklist:
            continue
        if clean.startswith("[") and clean.endswith("]"):
            continue
        if len(clean) < 4:
            continue
        if len(clean) > max_len:
            return clean[:max_len] + "..."
        return clean
    return ""
# 初始化 API 配置状态 (优先从本地加载)
local_config = load_api_config()
if "api_key" not in st.session_state:
    st.session_state.api_key = local_config["api_key"]
if "api_base" not in st.session_state:
    st.session_state.api_base = local_config["api_base"]
if "model_name" not in st.session_state:
    st.session_state.model_name = local_config["model_name"]
if "provider" not in st.session_state:
    st.session_state.provider = local_config.get("provider", "阿里云 (Qwen)")

# ==================== 全局状态初始化 ====================
if "chats" not in st.session_state:
    history = load_chat_history()
    st.session_state.chats = {}
    for chat_id, chat_data in history.get("chats", {}).items():
        st.session_state.chats[chat_id] = {
            "title": chat_data.get("title", f"新分析主题 {chat_id}"),
            "agent": None,
            "agent_messages": messages_from_dict(chat_data.get("agent_messages", []))
            if chat_data.get("agent_messages") else [],
            "ui_messages": chat_data.get("ui_messages", []),
        }
    st.session_state.current_chat_id = history.get("current_chat_id")
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None


def create_new_chat():
    """使用当前全局 API 配置创建新对话"""
    chat_id = str(uuid.uuid4())[:8]
    agent, sys_prompt = get_tumor_agent_and_prompt(
        api_key=st.session_state.api_key,
        base_url=st.session_state.api_base,
        model_name=st.session_state.model_name
    )
    st.session_state.chats[chat_id] = {
        "title": f"新分析主题 {chat_id}",
        "agent": agent,
        "agent_messages": [sys_prompt],
        "ui_messages": [{"role": "assistant", "content": "您好！我是生信助手。请告诉我您今天要分析什么数据？"}]
    }
    st.session_state.current_chat_id = chat_id
    save_chat_history()


if st.session_state.chats:
    if not st.session_state.current_chat_id or st.session_state.current_chat_id not in st.session_state.chats:
        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
elif st.session_state.api_key:
    create_new_chat()

# ==================== 侧边栏：配置与会话管理 ====================
with st.sidebar:
    st.title("⚙️ 大模型 API 配置")

    model_providers = {
        "阿里云 (Qwen)": {"base": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
        "DeepSeek": {"base": "https://api.deepseek.com", "model": "deepseek-chat"},
        "智谱 AI (GLM)": {"base": "https://open.bigmodel.cn/api/paas/v4/", "model": "glm-4"},
        "月之暗面 (Kimi)": {"base": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
        "OpenAI": {"base": "https://api.openai.com/v1", "model": "gpt-4o"},
        "自定义 (兼容 OpenAI 规范)": {"base": "", "model": ""}
    }

    # 恢复上次选中的提供商
    provider_index = list(model_providers.keys()).index(
        st.session_state.provider) if st.session_state.provider in model_providers else 0
    selected_provider = st.selectbox("选择模型厂商", list(model_providers.keys()), index=provider_index)

    default_base = model_providers[selected_provider][
        "base"] if selected_provider != "自定义 (兼容 OpenAI 规范)" else st.session_state.api_base
    default_model = model_providers[selected_provider][
        "model"] if selected_provider != "自定义 (兼容 OpenAI 规范)" else st.session_state.model_name

    input_base = st.text_input("Base URL", value=default_base)
    input_model = st.text_input("模型名称", value=default_model)
    input_key = st.text_input("API Key", type="password", value=st.session_state.api_key, placeholder="sk-...")

    if st.button("💾 保存配置并应用到新对话", type="primary", use_container_width=True):
        if not input_key:
            st.warning("⚠️ 请输入有效的 API Key！")
        else:
            # 更新 Session
            st.session_state.api_key = input_key
            st.session_state.api_base = input_base
            st.session_state.model_name = input_model
            st.session_state.provider = selected_provider
            # 保存到本地文件
            save_api_config(input_key, input_base, input_model, selected_provider)

            create_new_chat()
            st.success(f"✅ 配置已永久保存，已切换至 {input_model}！")
            st.rerun()

    st.divider()

    if st.session_state.api_key:
        st.title("📂 对话主题管理")
        if st.button("➕ 新建生信分析", use_container_width=True):
            create_new_chat()
            st.rerun()

        chat_ids_to_delete = []
        for chat_id, chat_data in st.session_state.chats.items():
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(chat_data["title"], key=f"btn_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    save_chat_history()
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{chat_id}"):
                    chat_ids_to_delete.append(chat_id)

        if chat_ids_to_delete:
            for cid in chat_ids_to_delete:
                del st.session_state.chats[cid]
                if st.session_state.current_chat_id == cid:
                    st.session_state.current_chat_id = list(st.session_state.chats.keys())[
                        0] if st.session_state.chats else None
                    if not st.session_state.current_chat_id:
                        create_new_chat()
            save_chat_history()
            st.rerun()

# ==================== 主界面区 ====================
if not st.session_state.api_key:
    st.info("👋 欢迎来到 OpenClaw 生信中枢！请先在左侧边栏填写并保存您的 **API Key** 以激活大脑。")
    st.stop()

st.title(f"🧬 OpenClaw - {st.session_state.chats[st.session_state.current_chat_id]['title']}")

current_chat = st.session_state.chats[st.session_state.current_chat_id]
ensure_chat_agent(current_chat)

for msg in current_chat["ui_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("请输入生信分析指令 (支持长文本粘贴)..."):
    current_chat["ui_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    current_chat["agent_messages"].append(HumanMessage(content=prompt))

    with st.chat_message("assistant"):
        status = st.status(f"🧠 {st.session_state.model_name} 正在接收指令并开始规划...", expanded=True)
        try:
            final_answer = ""
            for chunk in current_chat["agent"].stream({"messages": current_chat["agent_messages"]}):
                for node_name, state in chunk.items():
                    current_chat["agent_messages"].extend(state["messages"])

                    if node_name == "agent":
                        msg = state["messages"][-1]
                        if msg.content:
                            status.markdown(f"💭 **AI 思考**: *{msg.content}*")
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tc in msg.tool_calls:
                                status.markdown(f"🛠️ **准备调用工具**: `{tc['name']}` ...")
                        elif msg.content and not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                            final_answer = msg.content

                    elif node_name == "tools":
                        status.markdown(f"✅ **工具执行完毕**，正在将结果喂回给大模型...")

            status.update(label="🎉 流程执行完毕！", state="complete", expanded=False)
            st.markdown(final_answer)
            current_chat["ui_messages"].append({"role": "assistant", "content": final_answer})
            save_chat_history()

        except Exception as e:
            status.update(label="❌ 执行中断", state="error")
            st.error(f"❌ 大模型或工具运行异常: {str(e)}")
            save_chat_history()

    if len(current_chat["ui_messages"]) == 3:
        inferred = derive_title_from_ai(final_answer, max_len=16)
        if inferred:
            current_chat["title"] = inferred
        else:
            current_chat["title"] = prompt[:12] + "..."
        save_chat_history()
        st.rerun()
