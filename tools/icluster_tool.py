import os
from typing import List
from langchain_core.tools import tool
from tools.r_utils import run_r_script
from tools.tool_utils import resolve_output_dir, safe_path


@tool
def icluster_tool(data_paths: List[str], n_clusters: int, lambda_value: float = 0.2) -> str:
    """
    iCluster (2009)：R 包 iCluster 的整合聚类封装。
    参数：
    - data_paths: 多组学 CSV 路径列表（行=样本，列=特征，首列为样本ID）
    - n_clusters: 期望亚型数量
    - lambda_value: 惩罚项强度（默认 0.2）
    返回：聚类标签文件路径
    """
    if len(data_paths) < 2:
        return "⚠️ iCluster 至少需要 2 个组学数据文件。"

    output_dir = resolve_output_dir(data_paths, "iCluster")
    labels_path = os.path.join(output_dir, f"icluster_labels_k{n_clusters}.csv")
    r_script_path = os.path.join(output_dir, "run_icluster.R")

    data_lines = []
    vars_list = []
    for i, p in enumerate(data_paths, start=1):
        var = f"dt{i}"
        data_lines.append(f'{var} <- as.matrix(read.csv("{safe_path(p)}", row.names=1))')
        vars_list.append(var)
    data_list = "list(" + ", ".join(vars_list) + ")"

    r_code = f"""
    suppressPackageStartupMessages(library(iCluster))

    {os.linesep.join(data_lines)}
    data.list <- {data_list}

    fit <- iCluster(data.list, k={n_clusters}, lambda=rep({lambda_value}, length(data.list)))
    clusters <- fit$clusters
    sample_ids <- rownames(data.list[[1]])

    labels <- data.frame(Sample_ID=sample_ids, Subtype=paste0("Subtype_", clusters))
    write.csv(labels, file="{safe_path(labels_path)}", row.names=FALSE)
    cat(sprintf("\\n===R_OUTPUT_LABELS:{safe_path(labels_path)}===\\n"))
    """

    ok, out = run_r_script(r_code, r_script_path, timeout_sec=1200)
    if not ok:
        return f"⚠️ iCluster 运行失败：{out}"

    return (f"✅ iCluster 聚类完成！\n"
            f"标签已保存至：'{labels_path}'\n"
            f"可直接用于后续差异分析与可视化。")
