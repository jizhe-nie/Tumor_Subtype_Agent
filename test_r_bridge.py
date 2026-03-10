import subprocess
import os
import sys
import shutil


def find_rscript():
    # 1) 环境变量显式指定
    env_path = os.getenv("RSCRIPT_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    # 2) 系统 PATH 中查找
    rscript = "Rscript.exe" if os.name == "nt" else "Rscript"
    path_hit = shutil.which(rscript)
    if path_hit:
        return path_hit

    # 3) 常见安装路径兜底
    candidates = []
    if sys.platform == "darwin":
        candidates.extend([
            "/usr/local/bin/Rscript",
            "/opt/homebrew/bin/Rscript",
        ])
    elif os.name == "nt":
        # 常见 Windows 安装目录（按版本号排序再选最高）
        base_dirs = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        ]
        for base in base_dirs:
            r_base = os.path.join(base, "R")
            if os.path.isdir(r_base):
                versions = sorted(os.listdir(r_base), reverse=True)
                for v in versions:
                    candidates.append(os.path.join(r_base, v, "bin", "Rscript.exe"))

    for c in candidates:
        if os.path.exists(c):
            return c

    return None


def test_r_connection():
    print("正在尝试连接 R 语言环境...")

    # 自动查找 Rscript（兼容 macOS / Windows）
    rscript_path = find_rscript()

    # 检查这个路径到底对不对
    if not rscript_path or not os.path.exists(rscript_path):
        print("❌ 未找到 Rscript。")
        print("请确认已安装 R，并将 Rscript 加入 PATH，或设置环境变量 RSCRIPT_PATH 指向 Rscript/Rscript.exe。")
        return

    try:
        # 使用绝对路径调用 Rscript
        result = subprocess.run(
            [rscript_path, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ 连接成功！检测到 R 语言版本：")
        print(result.stdout.strip() or result.stderr.strip())

        # 进一步测试能否加载 ConsensusClusterPlus
        print("\n正在测试加载 ConsensusClusterPlus 包...")
        r_code = "library(ConsensusClusterPlus); print('Package loaded successfully!')"
        result2 = subprocess.run(
            [rscript_path, "-e", r_code],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ 算法包加载成功！")

    except subprocess.CalledProcessError as e:
        print(f"❌ 运行 R 代码失败，错误信息:\n{e.stderr}")
    except Exception as e:
        print(f"⚠️ 发生未知错误: {e}")


if __name__ == "__main__":
    test_r_connection()
