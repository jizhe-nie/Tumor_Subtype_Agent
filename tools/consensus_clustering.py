import os
from langchain_core.tools import tool
from tools.r_utils import run_r_script
from tools.tool_utils import safe_path


@tool
def consensus_clustering_tool(data_path: str, max_k: int = 6) -> str:
    """
    [高阶权威工具]：调用 R 语言官方 ConsensusClusterPlus 包进行一致性聚类。
    当你需要寻找肿瘤亚型最稳定、最优的数量（k 值）时，请调用此工具。
    参数：
    - data_path: 降维后的数据文件路径（CSV格式）。
    - max_k: 期望探索的最大亚型数量（默认测试到 6）。
    返回：最优 k 值的推荐，以及相关的评估图表（如 CDF 曲线）保存路径。
    """
    print(f"🧬 [Tool调用] 正在启动 R 语言后台执行 ConsensusClusterPlus (最大 k={max_k})...")

    if not os.path.exists(data_path):
        return f"⚠️ 错误：找不到数据文件 '{data_path}'。"

    try:
        # 1. 自动构建输出目录 (Output 路由)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.dirname(os.path.abspath(data_path))
        dataset_folder_name = os.path.basename(data_dir)
        if dataset_folder_name == "data":
            dataset_folder_name = os.path.basename(data_path).replace("pca_", "").replace("clean_", "").split(".")[0]

        output_dir = os.path.join(project_root, "output", dataset_folder_name, "ConsensusCluster")
        os.makedirs(output_dir, exist_ok=True)

        # 2. 转换路径格式（防止 R 语言在 Windows 下遇到 \ 会报错）
        safe_data_path = safe_path(data_path)
        safe_output_dir = safe_path(output_dir)

        # 3. 编写注入给 R 的执行脚本代码 (加入计算最优 k 值的 PAC 算法)
        r_code = f"""
        suppressPackageStartupMessages(library(ConsensusClusterPlus))

        # 读取数据并转置 (ConsensusClusterPlus 要求行是特征/PC，列是样本)
        data <- read.csv("{safe_data_path}", row.names=1)
        data_matrix <- t(as.matrix(data))

        # 运行权威的一致性聚类
        results <- ConsensusClusterPlus(
            d = data_matrix,
            maxK = {max_k},
            reps = 50,          # 快速重采样 50 次
            pItem = 0.8,        # 每次抽取 80% 的样本
            pFeature = 1,
            title = "{safe_output_dir}",
            clusterAlg = "km",
            distance = "euclidean",
            seed = 42,
            plot = "png"        # 让 R 自动帮我们画 CDF 等评估图！
        )

        # 使用生物信息学推荐的 PAC (Proportion of Ambiguous Clustering) 指标评估最优 K
        pac <- numeric({max_k})
        for(k in 2:{max_k}) {{
            cm <- results[[k]]$consensusMatrix
            # 计算处于 0.1 到 0.9 之间的模糊分配比例
            pac[k] <- sum(cm > 0.1 & cm < 0.9) / length(cm)
        }}
        # 寻找 PAC 最小的 k 值作为最优 k
        best_k <- which.min(pac[2:{max_k}]) + 1

        # 通过控制台将最优 k 值传回给 Python
        cat(sprintf("\\n===R_OUTPUT_OPTIMAL_K:%d===\\n", best_k))
        """

        # 4. 运行 R 脚本
        r_script_path = os.path.join(output_dir, "run_consensus.R")
        print("   - R 语言引擎正在进行高强度计算与画图，请耐心等待 (约需 10-30 秒)...")
        ok, out = run_r_script(r_code, r_script_path, timeout_sec=600)
        if not ok:
            return f"⚠️ R 脚本运行失败，错误信息:\n{out}"

        # 5. 从 R 的输出中解析出最优的 K 值
        best_k = None
        for line in out.split('\n'):
            if "===R_OUTPUT_OPTIMAL_K:" in line:
                best_k = line.split(":")[1].replace("===", "").strip()

        msg = (
            f"✅ 官方 ConsensusClusterPlus (R 语言版) 执行成功！\n"
            f"🏆 算法最终推荐：**基于 R 语言 PAC 指标计算的最优肿瘤亚型数量为 k={best_k}**。\n"
            f"📂 R 语言自动生成的官方图表（一致性矩阵热图、CDF 曲线等）已保存至专属目录：\n'{safe_output_dir}'\n"
            f"请使用这个最优 k 值进行下一步的 K-Means 最终聚类，并随后调用可视化工具生成最终散点图。"
        )
        return msg

    except Exception as e:
        return f"⚠️ 一致性聚类执行发生错误: {str(e)}"
