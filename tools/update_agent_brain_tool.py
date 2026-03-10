import os
import datetime
from langchain_core.tools import tool


@tool
def update_agent_brain_tool(target_file: str, content: str, mode: str = "append") -> str:
    """
    【核心工具】：Agent 自我进化与记忆更新器
    当你（大模型）发现需要长期记住的用户偏好、分析经验，或者需要修正自己的行为准则时，必须调用此工具！
    “好记性不如烂笔头”，任何仅存在于对话中的内容都会在刷新后消失，只有写入大脑文件才能永久保存。

    参数：
    - target_file: 必须是 "SOUL.md" (性格), "AGENTS.md" (行为规范), "MEMORY.md" (经验记忆) 或 "USER.md" (用户画像) 之一。
    - content: 你要写入的具体内容（需精简、精准）。
    - mode: "append"（默认，追加，推荐用于 MEMORY 和 USER） 或 "overwrite"（覆盖，极其谨慎使用！）。
    """
    allowed_files = ["SOUL.md", "AGENTS.md", "MEMORY.md", "USER.md"]
    if target_file not in allowed_files:
        return f"❌ 越权拦截：你被禁止修改 {target_file}。只能修改 {allowed_files}。"

    print(f"🧠 [意识上传] Agent 正在将思想写入 {target_file}...")

    try:
        # 动态定位到 agent_brain 文件夹
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        brain_dir = os.path.join(project_root, "agent_brain")
        os.makedirs(brain_dir, exist_ok=True)
        file_path = os.path.join(brain_dir, target_file)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        write_mode = "a" if mode == "append" else "w"

        with open(file_path, write_mode, encoding="utf-8") as f:
            if mode == "append":
                # 追加模式下，自动打上时间戳
                f.write(f"\n\n> [{timestamp}] 记忆追加:\n{content}\n")
            else:
                # 覆盖模式
                f.write(content)

        return f"✅ 意识固化成功！内容已安全写入 {target_file}。这部分记忆将在所有未来的会话中永久生效。"

    except Exception as e:
        return f"❌ 写入大脑时发生致命错误: {str(e)}"