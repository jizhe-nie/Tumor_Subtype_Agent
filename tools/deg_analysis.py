import pandas as pd
import numpy as np
from scipy import stats
import os
from langchain_core.tools import tool


@tool
def deg_analysis_tool(clean_data_path: str, labels_path: str, top_n: int = 10) -> str:
    """
    当你需要找出各个肿瘤亚型的“标志性差异基因 (Signature/Marker Genes)”时调用此工具。
    参数：
    - clean_data_path: 【清洗后的原始高维基因表达数据】的 CSV 路径 (注意：不要传降维后的数据，DEG 需要所有基因)。
    - labels_path: 聚类工具生成的【样本聚类标签名单】CSV 路径。
    - top_n: 每个亚型提取排名前几的标志基因（默认 10 个）。
    返回：差异基因分析报告及详细结果文件路径。
    """
    print(f"🧬 [Tool调用] 正在进行差异表达分析 (DEG)，寻找各亚型 Top {top_n} 标志基因...")

    if not os.path.exists(clean_data_path) or not os.path.exists(labels_path):
        return f"⚠️ 错误：数据文件或标签文件不存在，请核对路径。"

    try:
        # 1. 加载高维表达数据和标签
        expr_df = pd.read_csv(clean_data_path, index_col=0)
        labels_df = pd.read_csv(labels_path)

        # 确保样本能对齐
        merged = expr_df.merge(labels_df, left_index=True, right_on="Sample_ID")
        subtypes = merged["Subtype"].unique()

        all_markers = []
        summary_msg = f"✅ 差异表达分析 (DEG) 完成！各亚型 Top {top_n} 标志基因如下：\n"

        print("   - 正在进行高维特征统计检验，这可能需要十几秒钟...")

        # 2. 对每个亚型执行 "One vs Rest" 的差异分析
        for subtype in sorted(subtypes):
            # 划分两组：当前亚型 vs 其他所有亚型
            group_in = merged[merged["Subtype"] == subtype].drop(columns=["Sample_ID", "Subtype"])
            group_out = merged[merged["Subtype"] != subtype].drop(columns=["Sample_ID", "Subtype"])

            # 计算表达均值和 Log2 差异倍数 (Fold Change)
            mean_in = group_in.mean()
            mean_out = group_out.mean()
            # 加上一个极小值 1e-5 避免除以 0
            log2fc = np.log2((mean_in + 1e-5) / (mean_out + 1e-5))

            # 执行 T 检验获取 p-value
            t_stat, p_vals = stats.ttest_ind(group_in, group_out, equal_var=False)

            # 整理结果表
            res_df = pd.DataFrame({
                "Gene": expr_df.columns,
                "Log2FC": log2fc.values,
                "p_value": p_vals
            })

            # 过滤掉 NaN，按 Log2FC (高表达) 和 p_value (显著性) 排序寻找标志基因
            res_df = res_df.dropna()
            # 选出上调基因 (Log2FC > 0)，并按 p_value 升序
            up_regulated = res_df[res_df["Log2FC"] > 0].sort_values(by="p_value")
            top_genes = up_regulated.head(top_n)

            # 记录文本摘要
            gene_list = ", ".join(top_genes["Gene"].tolist())
            summary_msg += f"🔹 **{subtype}**: {gene_list}\n"

            # 给数据打上亚型标签，合并用于保存
            top_genes["Target_Subtype"] = subtype
            all_markers.append(top_genes)

        # 3. 将完整的 Marker 基因表保存到 output 目录
        final_markers_df = pd.concat(all_markers, ignore_index=True)

        output_dir = os.path.dirname(labels_path)
        output_file = os.path.join(output_dir, "subtype_marker_genes.csv")
        final_markers_df.to_csv(output_file, index=False)

        summary_msg += f"\n💾 完整的 DEG 统计学指标（包含 p-value 和 Log2FC）已保存至: '{output_file}'。"
        return summary_msg

    except Exception as e:
        return f"⚠️ 差异分析执行发生错误: {str(e)}"