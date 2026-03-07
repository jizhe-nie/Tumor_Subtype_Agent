import os
import sys
import importlib
import inspect

# 🌟 增加这一行：确保系统能正确找到根目录，防止 import tools 失败
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 🌟 核心修改：直接导入 LangChain 的工具基类
from langchain_core.tools import BaseTool


def load_all_skills(tools_dir="../tools"):
    """
    [类似 OpenClaw 的技能加载器]
    自动扫描 tools 文件夹下的所有 Python 文件，加载所有 LangChain Tool。
    """
    skills = []

    # 获取 tools 目录的绝对路径
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), tools_dir))

    print("🛠️ [Skill Manager] 正在扫描并加载技能库...")

    # 防止路径不存在的小错误
    if not os.path.exists(base_path):
        print(f"❌ 找不到技能目录，请检查路径: {base_path}")
        return skills

    # 遍历 tools 文件夹下的所有文件
    for filename in os.listdir(base_path):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]  # 去掉 .py 后缀

            try:
                # 动态导入模块
                module = importlib.import_module(f"tools.{module_name}")

                # 遍历文件里的所有对象
                for name, obj in inspect.getmembers(module):
                    # 🌟 终极判断法：只要它是 BaseTool 的实例，就绝对是我们要的技能！
                    if isinstance(obj, BaseTool):
                        skills.append(obj)
                        print(f"  -> 已成功加载技能: 【{obj.name}】")

            except Exception as e:
                print(f"  -> ⚠️ 加载 {filename} 时出错: {e}")

    print(f"✅ [Skill Manager] 技能库加载完毕，共装备 {len(skills)} 个技能！\n")
    return skills


# 本地测试
if __name__ == "__main__":
    loaded_skills = load_all_skills()