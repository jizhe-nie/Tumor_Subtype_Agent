import subprocess
import os


def test_r_connection():
    print("正在尝试连接 R 语言环境...")

    # 🌟 核心修改：直接写死 Rscript 的绝对路径，完美绕过系统环境变量问题！
    rscript_path = r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"

    # 检查这个路径到底对不对
    if not os.path.exists(rscript_path):
        print(f"❌ 找不到文件: {rscript_path}")
        print("请检查你的 R 是否真的安装在这个路径下，如果不是，请把上面的路径改成你电脑里实际的 Rscript.exe 路径。")
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