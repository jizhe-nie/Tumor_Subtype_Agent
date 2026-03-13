import os
from typing import List
from langchain_core.tools import tool
from tools.r_utils import run_r_script
from tools.tool_utils import resolve_output_dir, safe_path


@tool
def pinsplus_tool(
    data_paths: List[str],
    n_clusters: int,
    data_types: List[str] | None = None,
) -> str:
    """
    PINSPlus (2019)：R 包 PINSPlus 的扰动聚类与多组学整合。
    参数：
    - data_paths: 多组学 CSV 路径列表（行=样本，列=特征）
    - n_clusters: 期望亚型数量
    - data_types: 与 data_paths 对应的组学类型（如 "RNA","CNV","METH"），可选
    返回：聚类标签文件路径
    """
    if len(data_paths) < 2:
        return "⚠️ PINSPlus 至少需要 2 个组学数据文件。"

    output_dir = resolve_output_dir(data_paths, "PINSPlus")
    labels_path = os.path.join(output_dir, f"pinsplus_labels_k{n_clusters}.csv")
    r_script_path = os.path.join(output_dir, "run_pinsplus.R")

    data_lines = []
    vars_list = []
    for i, p in enumerate(data_paths, start=1):
        var = f"dt{i}"
        data_lines.append(f'{var} <- as.matrix(read.csv("{safe_path(p)}", row.names=1))')
        vars_list.append(var)
    data_list = "list(" + ", ".join(vars_list) + ")"
    if data_types and len(data_types) == len(data_paths):
        type_vec = "c(" + ", ".join([f'"{t}"' for t in data_types]) + ")"
    else:
        type_vec = "NULL"

    r_code = f"""
    suppressPackageStartupMessages(library(PINSPlus))

    {os.linesep.join(data_lines)}
    data.list <- {data_list}

    res <- SubtypingOmicsData(
        datalist = data.list,
        data.type = {type_vec},
        K = {n_clusters}
    )

    clusters <- NULL
    if (!is.null(res$clustering)) {{
        clusters <- res$clustering
    }} else if (!is.null(res$final.clustering)) {{
        clusters <- res$final.clustering
    }} else if (!is.null(res$cluster)) {{
        clusters <- res$cluster
    }}

    if (is.null(clusters)) {{
        stop("无法从 PINSPlus 结果中解析 clusters。")
    }}

    sample_ids <- rownames(data.list[[1]])
    labels <- data.frame(Sample_ID=sample_ids, Subtype=paste0("Subtype_", clusters))
    write.csv(labels, file="{safe_path(labels_path)}", row.names=FALSE)
    cat(sprintf("\\n===R_OUTPUT_LABELS:{safe_path(labels_path)}===\\n"))
    """

    ok, out = run_r_script(r_code, r_script_path, timeout_sec=1800)
    if not ok:
        return f"⚠️ PINSPlus 运行失败：{out}"

    return (f"✅ PINSPlus 聚类完成！\n"
            f"标签已保存至：'{labels_path}'\n"
            f"可直接用于后续差异分析与可视化。")
