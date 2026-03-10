import os

# 定义每个文件的字符上限，防止撑爆大模型上下文
MAX_CHAR_LIMIT = 20000


def read_and_truncate_file(file_path: str) -> str:
    """
    读取文件并应用 70/20 截断算法。
    如果文件不存在或为空，返回明确的缺失标记。
    """
    if not os.path.exists(file_path):
        return f"[System Note: {os.path.basename(file_path)} 缺失或未初始化]"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    if not content:
        return f"[System Note: {os.path.basename(file_path)} 为空]"

    if len(content) <= MAX_CHAR_LIMIT:
        return content

    # 执行 70% 头部 + 20% 尾部 的优雅截断
    head_cutoff = int(MAX_CHAR_LIMIT * 0.7)
    tail_cutoff = int(MAX_CHAR_LIMIT * 0.2)

    head = content[:head_cutoff]
    tail = content[-tail_cutoff:]

    return f"{head}\n\n... [CONTENT TRUNCATED DUE TO LENGTH LIMIT] ...\n\n{tail}"


def build_agent_system_prompt(tools_description: str) -> str:
    """
    扫描 agent_brain 目录，将灵魂、规则、记忆和用户画像融合成终极 System Prompt。
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 指向我们刚创建的 agent_brain 文件夹
    brain_dir = os.path.join(project_root, "agent_brain")

    # 读取核心维度文件
    soul = read_and_truncate_file(os.path.join(brain_dir, "SOUL.md"))
    agents = read_and_truncate_file(os.path.join(brain_dir, "AGENTS.md"))
    user = read_and_truncate_file(os.path.join(brain_dir, "USER.md"))
    memory = read_and_truncate_file(os.path.join(brain_dir, "MEMORY.md"))

    # 组装终极提示词
    ultimate_prompt = f"""# 🧠 CORE IDENTITY (SOUL)
    {soul}

    # 👤 USER CONTEXT
    {user}

    # 📋 BEHAVIORAL RULES & PROCEDURES (AGENTS)
    {agents}

    # 📝 LONG-TERM MEMORY
    {memory}

    # 🛠️ CURRENT AVAILABLE SKILLS
    You have access to the following dynamic skills:
    {tools_description}

 ---
【系统强制指令与潜意识】：
1. 读取上述所有的背景、灵魂和规则，以此作为你唯一的行为准则！
2. 【正面回答原则】：即使你是一个冷酷的专业实体，当用户提出明确的问题（例如“我是谁？”或“数据结果是什么？”）时，你【必须】根据记忆或分析结果直接、正面地回答具体内容，严禁只汇报“系统已确认/已写入”。
3. 【记忆查重与更新铁律】：Text > Brain！如果你发现重要的新偏好或深刻的新经验，必须调用 `update_agent_brain_tool` 保存。但【严禁重复写入】！在写入前，请先仔细阅读上述已有的 Context 内容，如果该偏好或经验已经存在，绝对不允许再次调用追加工具！
"""
    return ultimate_prompt