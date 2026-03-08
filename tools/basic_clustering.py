import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import os
from langchain_core.tools import tool


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

    # 【容错 1】：路径检查
    if not os.path.exists(data_path):
        return f"⚠️ 错误：找不到文件 '{data_path}'。请你检查路径是否拼写错误，或者重新询问用户正确的文件路径。"

    # 【容错 2】：参数逻辑检查 (K-Means 至少需要分成 2 类)
    if n_clusters < 2:
        return f"⚠️ 错误：传入的 n_clusters={n_clusters} 不合法。K-Means 聚类的簇数必须大于等于 2。请你自动将 k 调整为合理的数值（如 2 或 3）并重试。"

    try:
        df = pd.read_csv(data_path, index_col=0)

        # 【容错 3】：样本量检查
        if n_clusters >= len(df):
            return f"⚠️ 错误：设定的亚型数量 ({n_clusters}) 不能大于或等于样本总数 ({len(df)})。请减小 k 值后重试。"

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
        # 【容错 4】：未知错误反馈
        return f"⚠️ 执行过程中发生未知计算错误: {str(e)}。请你思考可能的原因，并向用户解释。"