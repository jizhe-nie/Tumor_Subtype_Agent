import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import os
from langchain_core.tools import tool


@tool
def kmeans_clustering_tool(data_path: str, n_clusters: int) -> str:
    """
    当你需要对数据进行最终的聚类分析，并获取每个样本的亚型归属名单时调用此工具。
    参数：
    - data_path: 降维后或清洗后的 CSV 数据文件路径。
    - n_clusters: 期望寻找的亚型数量（k 值）。
    返回：包含评估指标以及【样本聚类标签文件】保存路径的报告。
    """
    print(f"🔧 [Tool调用] 正在执行 K-Means 聚类并保存样本名单 (k={n_clusters})...")

    if not os.path.exists(data_path):
        return f"⚠️ 错误：找不到文件 '{data_path}'。"

    try:
        df = pd.read_csv(data_path, index_col=0)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(df)
        score = silhouette_score(df, cluster_labels)

        # 统计分布
        unique, counts = np.unique(cluster_labels, return_counts=True)
        cluster_distribution = dict(zip([f"亚型_{i + 1}" for i in unique], counts))

        # 🌟 核心升级：保存具体的样本分类名单
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.dirname(os.path.abspath(data_path))
        dataset_name = os.path.basename(data_dir)
        if dataset_name == "data":
            dataset_name = os.path.basename(data_path).replace("pca_", "").replace("clean_", "").split(".")[0]

        output_dir = os.path.join(project_root, "output", dataset_name)
        os.makedirs(output_dir, exist_ok=True)

        # 生成标签 DataFrame 并保存
        labels_df = pd.DataFrame({
            "Sample_ID": df.index,
            "Subtype": [f"Subtype_{i + 1}" for i in cluster_labels]
        })
        labels_file_path = os.path.join(output_dir, f"cluster_labels_k{n_clusters}.csv")
        labels_df.to_csv(labels_file_path, index=False)

        result_msg = (
            f"✅ K-Means 聚类执行成功！\n"
            f"⭐ 轮廓系数: {score:.4f} | 👥 分布: {cluster_distribution}\n"
            f"💾 **聚类标签名单已保存至**: '{labels_file_path}'。\n"
            f"提示：如果后续需要做差异表达分析 (DEG)，请将清洗后的原始高维数据路径和此标签名单路径一起传给 DEG 工具。"
        )
        return result_msg
    except Exception as e:
        return f"⚠️ 聚类执行发生错误: {str(e)}"