import os
import numpy as np
import pandas as pd
from typing import List
from langchain_core.tools import tool
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances
from tools.tool_utils import resolve_output_dir


def _density_kmeanspp_init(X: np.ndarray, n_clusters: int, random_state: int = 42):
    rng = np.random.RandomState(random_state)
    dists = pairwise_distances(X, metric="euclidean")
    sigma = np.median(dists)
    if sigma == 0:
        sigma = 1e-6
    density = np.sum(np.exp(- (dists ** 2) / (2 * sigma ** 2)), axis=1)

    centers = []
    first_idx = np.argmax(density)
    centers.append(first_idx)

    for _ in range(1, n_clusters):
        dist_to_centers = np.min(dists[:, centers], axis=1)
        probs = density * (dist_to_centers ** 2)
        if probs.sum() == 0:
            next_idx = rng.choice(len(X))
        else:
            probs = probs / probs.sum()
            next_idx = rng.choice(len(X), p=probs)
        centers.append(next_idx)

    return X[centers]


@tool
def dkmpp_tool(data_path: str, n_clusters: int) -> str:
    """
    DKMPP (2017)：密度 K-Means++ 初始化 + KMeans 聚类。
    参数：
    - data_path: CSV 文件路径（行=样本，列=特征）
    - n_clusters: 期望亚型数量
    返回：聚类标签文件路径
    """
    if not os.path.exists(data_path):
        return f"⚠️ 找不到数据文件：{data_path}"

    output_dir = resolve_output_dir([data_path], "DKMPP")
    labels_path = os.path.join(output_dir, f"dkmpp_labels_k{n_clusters}.csv")

    df = pd.read_csv(data_path, index_col=0)
    X = df.values.astype(float)
    centers = _density_kmeanspp_init(X, n_clusters=n_clusters, random_state=42)

    km = KMeans(n_clusters=n_clusters, init=centers, n_init=1, random_state=42)
    labels = km.fit_predict(X)

    result_df = pd.DataFrame({
        "Sample_ID": df.index.tolist(),
        "Subtype": [f"Subtype_{l + 1}" for l in labels],
    })
    result_df.to_csv(labels_path, index=False)

    return (f"✅ DKMPP 聚类完成！\n"
            f"标签已保存至：'{labels_path}'\n"
            f"可直接用于后续差异分析与可视化。")
