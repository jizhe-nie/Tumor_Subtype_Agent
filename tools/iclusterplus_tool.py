import os
from typing import List
from langchain_core.tools import tool
from tools.r_utils import run_r_script
from tools.tool_utils import resolve_output_dir, safe_path


@tool
def iclusterplus_tool(data_paths: List[str], n_clusters: int, lambda_value: float = 1.0) -> str:
    """
    iClusterPlus (2013)：R 包 iClusterPlus 的多组学聚类封装。
    参数：
    - data_paths: 多组学 CSV 路径列表（行=样本，列=特征）
    - n_clusters: 期望亚型数量
    - lambda_value: 惩罚项强度（默认 1.0）
    返回：聚类标签文件路径
    """
    if len(data_paths) < 2:
        return "⚠️ iClusterPlus 至少需要 2 个组学数据文件。"

    output_dir = resolve_output_dir(data_paths, "iClusterPlus")
    labels_path = os.path.join(output_dir, f"iclusterplus_labels_k{n_clusters}.csv")
    r_script_path = os.path.join(output_dir, "run_iclusterplus.R")

    data_lines = []
    vars_list = []
    for i, p in enumerate(data_paths, start=1):
        var = f"dt{i}"
        data_lines.append(f'{var} <- as.matrix(read.csv("{safe_path(p)}", row.names=1))')
        vars_list.append(var)
    data_args = ", ".join(vars_list)
    type_vec = "c(" + ", ".join(['"gaussian"'] * len(vars_list)) + ")"
    lambda_vec = "c(" + ", ".join([str(lambda_value)] * len(vars_list)) + ")"

    r_code = f"""
    suppressPackageStartupMessages(library(iClusterPlus))

    {os.linesep.join(data_lines)}

    fit <- iClusterPlus({data_args}, type={type_vec}, K={n_clusters}, lambda={lambda_vec})
    clusters <- fit$clusters
    sample_ids <- rownames({vars_list[0]})

    labels <- data.frame(Sample_ID=sample_ids, Subtype=paste0("Subtype_", clusters))
    write.csv(labels, file="{safe_path(labels_path)}", row.names=FALSE)
    cat(sprintf("\\n===R_OUTPUT_LABELS:{safe_path(labels_path)}===\\n"))
    """

    ok, out = run_r_script(r_code, r_script_path, timeout_sec=1800)
    if not ok:
        return f"⚠️ iClusterPlus 运行失败：{out}"

    return (f"✅ iClusterPlus 聚类完成！\n"
            f"标签已保存至：'{labels_path}'\n"
            f"可直接用于后续差异分析与可视化。")
