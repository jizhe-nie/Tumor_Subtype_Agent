import os
from typing import List
from langchain_core.tools import tool
from tools.r_utils import run_r_script
from tools.tool_utils import resolve_output_dir, safe_path


@tool
def iclusterbayes_tool(
    data_paths: List[str],
    n_clusters: int,
    n_burnin: int = 200,
    n_draw: int = 200,
) -> str:
    """
    iClusterBayes (2018)：iClusterPlus 包内的 Bayesian iCluster。
    参数：
    - data_paths: 多组学 CSV 路径列表（行=样本，列=特征）
    - n_clusters: 期望亚型数量
    - n_burnin: MCMC burn-in 次数
    - n_draw: MCMC 抽样次数
    返回：聚类标签文件路径
    """
    if len(data_paths) < 2:
        return "⚠️ iClusterBayes 至少需要 2 个组学数据文件。"

    output_dir = resolve_output_dir(data_paths, "iClusterBayes")
    labels_path = os.path.join(output_dir, f"iclusterbayes_labels_k{n_clusters}.csv")
    r_script_path = os.path.join(output_dir, "run_iclusterbayes.R")

    data_lines = []
    vars_list = []
    for i, p in enumerate(data_paths, start=1):
        var = f"dt{i}"
        data_lines.append(f'{var} <- as.matrix(read.csv("{safe_path(p)}", row.names=1))')
        vars_list.append(var)
    data_args = ", ".join(vars_list)
    type_vec = "c(" + ", ".join(['"gaussian"'] * len(vars_list)) + ")"

    r_code = f"""
    suppressPackageStartupMessages(library(iClusterPlus))

    {os.linesep.join(data_lines)}

    fit <- iClusterBayes({data_args}, type={type_vec}, K={n_clusters}, n.burnin={n_burnin}, n.draw={n_draw})

    clusters <- NULL
    if (!is.null(fit$clusters)) {{
        clusters <- fit$clusters
    }} else if (!is.null(fit$cluster)) {{
        clusters <- fit$cluster
    }} else if (!is.null(fit$Z)) {{
        clusters <- apply(fit$Z, 1, which.max)
    }} else if (!is.null(fit$expZ)) {{
        clusters <- apply(fit$expZ, 1, which.max)
    }}

    if (is.null(clusters)) {{
        stop("无法从 iClusterBayes 结果中解析 clusters。")
    }}

    sample_ids <- rownames({vars_list[0]})
    labels <- data.frame(Sample_ID=sample_ids, Subtype=paste0("Subtype_", clusters))
    write.csv(labels, file="{safe_path(labels_path)}", row.names=FALSE)
    cat(sprintf("\\n===R_OUTPUT_LABELS:{safe_path(labels_path)}===\\n"))
    """

    ok, out = run_r_script(r_code, r_script_path, timeout_sec=1800)
    if not ok:
        return f"⚠️ iClusterBayes 运行失败：{out}"

    return (f"✅ iClusterBayes 聚类完成！\n"
            f"标签已保存至：'{labels_path}'\n"
            f"可直接用于后续差异分析与可视化。")
