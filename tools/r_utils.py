import os
import sys
import shutil
import subprocess


def find_rscript():
    env_path = os.getenv("RSCRIPT_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    rscript = "Rscript.exe" if os.name == "nt" else "Rscript"
    path_hit = shutil.which(rscript)
    if path_hit:
        return path_hit

    candidates = []
    if sys.platform == "darwin":
        candidates.extend([
            "/usr/local/bin/Rscript",
            "/opt/homebrew/bin/Rscript",
        ])
    elif os.name == "nt":
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


def run_r_script(r_code: str, script_path: str, timeout_sec: int = 600):
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(r_code)

    rscript_path = find_rscript()
    if not rscript_path:
        return False, "未找到 Rscript。请安装 R 并配置 PATH 或设置 RSCRIPT_PATH。"

    try:
        result = subprocess.run(
            [rscript_path, script_path],
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout_sec,
        )
        return True, result.stdout
    except subprocess.TimeoutExpired:
        return False, f"R 脚本执行超时（>{timeout_sec}s）"
    except subprocess.CalledProcessError as e:
        return False, (e.stderr.strip() or e.stdout.strip())
