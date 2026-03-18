import os
import subprocess
import re
from langchain_core.tools import tool

@tool
def sandbox_execution_tool(code: str) -> str:
    """
    【核心工具】：安全的 Python 代码沙盒执行器。
    当你（Agent）需要尝试新的算法参数、验证数据维度、进行数据拼接、或者写一段临时脚本来计算评估指标（如轮廓系数）时，【必须】使用此工具！
    
    参数：
    - code: 你要执行的完整 Python 代码。请确保代码包含必要的 import 语句，并通过 print() 输出你想要观察的结果。
    
    返回：
    - 代码执行的标准输出 (stdout) 或 详细的报错追踪 (stderr)。如果你看到报错，请分析原因并修改代码重新执行！
    """
    
    # 1. 代码清洗：去除大模型经常附带的 Markdown 代码块标记 (```python ... ```)
    cleaned_code = re.sub(r"^```python\n", "", code)
    cleaned_code = re.sub(r"^```\n", "", cleaned_code)
    cleaned_code = re.sub(r"\n```$", "", cleaned_code)
    
    # 2. 准备沙盒物理环境
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sandbox_dir = os.path.join(project_root, "workspace") # 临时工作区
    os.makedirs(sandbox_dir, exist_ok=True)
    
    script_path = os.path.join(sandbox_dir, "temp_sandbox_script.py")
    
    # 3. 将清理后的代码写入物理文件
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(cleaned_code)
    except Exception as e:
        return f"❌ 沙盒内部错误：无法写入临时脚本文件 - {str(e)}"
        
    # 4. 黑盒隔离运行 (Subprocess)
    print("🛡️ [沙盒启动] 正在隔离环境中执行 Agent 生成的代码...")
    try:
        # 设置 timeout 防止 Agent 写出死循环代码导致系统卡死
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            timeout=60  # 核心保护机制：最长允许运行 60 秒
        )
        
        # 5. 组装执行报告返回给大模型
        output = ""
        if result.stdout:
            output += f"✅ [标准输出 (STDOUT)]:\n{result.stdout}\n"
        if result.stderr:
            output += f"⚠️ [标准错误/警告 (STDERR)]:\n{result.stderr}\n"
            
        if result.returncode != 0:
            return f"❌ 代码执行失败 (返回码 {result.returncode})！请仔细阅读以下报错信息并修正你的代码：\n{output}"
            
        return output if output else "✅ 代码执行成功，但没有产生任何终端输出 (没有 print)。"
        
    except subprocess.TimeoutExpired:
        return "❌ 严重错误：代码执行超时 (超过60秒) 被系统强制杀掉！可能是出现了死循环，或者是计算量过大。请优化你的算法复杂度。"
    except Exception as e:
        return f"❌ 未知环境执行错误: {str(e)}"