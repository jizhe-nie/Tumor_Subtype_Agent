import os
from typing import List
from langchain_core.tools import tool
from tools.r_utils import run_r_script
from tools.tool_utils import resolve_output_dir, safe_path


@tool
def cimlr_tool(
    data_paths: List[str],
    n_clusters: int,
    cores_ratio: float = 1.0,
) -> str:
    """
    CIMLR (2018)：R 包 CIMLR 的多核学习整合聚类封装。
    参数：
    - data_paths: 多组学 CSV 路径列表（行=样本，列=特征）
    - n_clusters: 期望亚型数量
    - cores_ratio: 并行核心比例（默认 1.0）
    返回：聚类标签文件路径
    """
    if len(data_paths) < 2:
        return "⚠️ CIMLR 至少需要 2 个组学数据文件。"

    output_dir = resolve_output_dir(data_paths, "CIMLR")
    labels_path = os.path.join(output_dir, f"cimlr_labels_k{n_clusters}.csv")
    r_script_path = os.path.join(output_dir, "run_cimlr.R")

    data_lines = []
    vars_list = []
    for i, p in enumerate(data_paths, start=1):
        var = f"dt{i}"
        data_lines.append(f'{var} <- as.matrix(read.csv("{safe_path(p)}", row.names=1))')
        vars_list.append(var)
    data_list = "list(" + ", ".join(vars_list) + ")"

    r_code = f"""
    suppressPackageStartupMessages(library(CIMLR))

    {os.linesep.join(data_lines)}
    data.list <- {data_list}

    fit <- CIMLR(data.list, c={n_clusters}, cores.ratio={cores_ratio})
    clusters <- fit$y$cluster
    sample_ids <- rownames(data.list[[1]])

    labels <- data.frame(Sample_ID=sample_ids, Subtype=paste0("Subtype_", clusters))
    write.csv(labels, file="{safe_path(labels_path)}", row.names=FALSE)
    cat(sprintf("\\n===R_OUTPUT_LABELS:{safe_path(labels_path)}===\\n"))
    """

    ok, out = run_r_script(r_code, r_script_path, timeout_sec=1800)
    if not ok:
        return f"⚠️ CIMLR 运行失败：{out}"

    return (f"✅ CIMLR 聚类完成！\n"
            f"标签已保存至：'{labels_path}'\n"
            f"可直接用于后续差异分析与可视化。")
