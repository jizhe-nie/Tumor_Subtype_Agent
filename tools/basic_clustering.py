import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import os
from langchain_core.tools import tool  # 🌟 引入 tool 装饰器


@tool
def kmeans_clustering_tool(data_path: str, n_clusters: int) -> str:
    """
    当你需要对基因表达数据进行聚类分析（寻找肿瘤亚型）时使用此工具。
    参数：
    - data_path: 数据的 CSV 文件路径。
    - n_clusters: 期望寻找的亚型数量（正整数，通常在 2 到 10 之间）。
    返回包含数据概况、轮廓系数评估以及各亚型样本分布的文本报告。
    """
    print(f"🔧 [Tool调用] 正在使用 K-Means 算法处理数据: {data_path} (k={n_clusters})...")

    if not os.path.exists(data_path):
        return f"执行失败：找不到数据文件 {data_path}，请检查路径。"

    try:
        df = pd.read_csv(data_path, index_col=0)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(df)
        score = silhouette_score(df, cluster_labels)
        unique, counts = np.unique(cluster_labels, return_counts=True)
        cluster_distribution = dict(zip([f"亚型_{i + 1}" for i in unique], counts))

        result_msg = (
            f"✅ K-Means 聚类执行成功！\n"
            f"📊 数据概况: 包含 {df.shape[0]} 个样本, {df.shape[1]} 个特征。\n"
            f"🔍 设定的亚型数量 (k): {n_clusters}\n"
            f"⭐ 轮廓系数 (Silhouette Score): {score:.4f}\n"
            f"👥 各亚型样本分布: {cluster_distribution}\n"
        )
        return result_msg
    except Exception as e:
        return f"执行过程中发生错误: {str(e)}"