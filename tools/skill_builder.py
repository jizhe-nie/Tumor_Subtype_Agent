import os
import sys
import uuid
import subprocess
from langchain_core.tools import tool


def _run_subprocess(cmd, timeout_sec=8):
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout_sec,
        )
        return True, (result.stdout.strip() or result.stderr.strip())
    except subprocess.TimeoutExpired:
        return False, f"超时（>{timeout_sec}s）"
    except subprocess.CalledProcessError as e:
        return False, (e.stderr.strip() or e.stdout.strip())


def _black_box_import_test(py_file_path: str):
    # 用子进程隔离导入，避免污染当前进程
    probe_code = (
        "import importlib.util, sys;"
        "spec=importlib.util.spec_from_file_location('tmp_skill', sys.argv[1]);"
        "m=importlib.util.module_from_spec(spec);"
        "spec.loader.exec_module(m);"
        "print('OK')"
    )
    return _run_subprocess([sys.executable, "-c", probe_code, py_file_path], timeout_sec=8)


@tool
def create_new_skill_tool(skill_filename: str, code_content: str) -> str:
    """
    [造物主核心工具]：专门用于动态扩充 Agent 自身的技能库。
    当你（Agent）根据文献或用户提示，编写好了一个全新的算法工具代码后，
    在【取得用户同意】的前提下，调用此工具将代码永久写入系统。

    参数：
    - skill_filename: 要保存的文件名（必须以 .py 结尾，例如 'snf_clustering.py'）。
    - code_content: 完整的 Python 工具代码字符串（必须包含 @tool 装饰器、详细的中文注释和完整的 import）。

    返回：写入结果的状态报告。
    """
    print(f"🔨 [系统操作] 正在将新技能 {skill_filename} 永久写入底层架构...")

    try:
        # 寻找 tools 目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tools_dir = os.path.join(project_root, "tools")

        # 检查文件名合法性
        if not skill_filename.endswith(".py"):
            return "⚠️ 错误：技能文件名必须以 .py 结尾。"

        file_path = os.path.join(tools_dir, skill_filename)
        tmp_path = os.path.join(tools_dir, f".__tmp_{uuid.uuid4().hex}.py")

        # 先写入临时文件
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code_content)

        # 1) 语法预编译检查
        ok, msg = _run_subprocess([sys.executable, "-m", "py_compile", tmp_path], timeout_sec=8)
        if not ok:
            os.remove(tmp_path)
            return f"⚠️ 代码语法检查失败（已拦截，未写入正式技能库）: {msg}"

        # 2) 黑盒导入测试（子进程）
        ok, msg = _black_box_import_test(tmp_path)
        if not ok:
            os.remove(tmp_path)
            return f"⚠️ 黑盒导入测试失败（已拦截，未写入正式技能库）: {msg}"

        # 通过校验后再落盘
        os.replace(tmp_path, file_path)

        return f"✅ 新技能写入成功！文件已保存至：{file_path}。请通知用户：在下次重启 Agent 时，此新技能将自动生效！"

    except Exception as e:
        return f"⚠️ 写入技能文件失败: {str(e)}"
