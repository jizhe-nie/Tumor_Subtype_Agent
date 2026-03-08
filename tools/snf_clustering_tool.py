import os
from typing import List
import pandas as pd
import numpy as np
from sklearn.cluster import SpectralClustering
from sklearn.metrics import pairwise_distances
from langchain_core.tools import tool


def compute_affinity(X, K=20):
    """手写亲和矩阵，完美绕开 snfpy 的库冲突报错"""
    dists = pairwise_distances(X, metric='euclidean')
    n = dists.shape[0]
    W = np.zeros((n, n))
    for i in range(n):
        idx = np.argsort(dists[i])[:K + 1]  # 取最近的 K 个邻居
        sigma = np.median(dists[i, idx])
        if sigma == 0: sigma = 1e-5
        W[i, idx] = np.exp(- (dists[i, idx] ** 2) / (2 * sigma ** 2))
        W[idx, i] = W[i, idx]  # 保证对称
    np.fill_diagonal(W, 1.0)
    return W


def snf_fusion(affinities, t=20):
    """手写多组学融合，完美绕开 snfpy 的库冲突报错"""
    W = [A.copy() for A in affinities]
    for i in range(len(W)):
        W[i] = W[i] / (np.sum(W[i], axis=1, keepdims=True) + 1e-10)

    for _ in range(t):
        W_new = []
        for i in range(len(W)):
            sum_others = np.sum([W[j] for j in range(len(W)) if j != i], axis=0)
            W_temp = W[i] @ sum_others @ W[i].T
            row_sums = np.sum(W_temp, axis=1, keepdims=True)
            W_new.append(W_temp / (row_sums + 1e-10))
        W = [(wn + wn.T) / 2 for wn in W_new]

    final_W = np.mean(W, axis=0)
    np.fill_diagonal(final_W, 1.0)
    return final_W


@tool
def snf_clustering_tool(data_paths: List[str], n_clusters: int) -> str:
    """
    【核心工具】：SNF 多组学联合融合聚类
    当你需要对多份组学数据进行 SNF 融合和聚类时调用此工具。
    参数：
    - data_paths: 至少包含两个 CSV 文件路径的列表。
    - n_clusters: 期望聚类的亚型数量。
    返回：聚类标签文件保存的路径（可直接作为 labels_path 传给差异分析工具）。
    """
    print(f"🧬 [Tool调用] 正在执行无依赖版 SNF 多组学融合聚类 (k={n_clusters})...")

    try:
        # 构建输出目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dataset_name = os.path.basename(os.path.dirname(data_paths[0]))
        if dataset_name == "data": dataset_name = "multi_omics_snf"
        output_dir = os.path.join(project_root, "output", dataset_name)
        os.makedirs(output_dir, exist_ok=True)

        # 1. 读取数据并构建亲和矩阵
        affinities = []
        sample_ids = None
        for path in data_paths:
            df = pd.read_csv(path, index_col=0)
            if sample_ids is None: sample_ids = df.index.tolist()
            X = df.values.astype(float)
            W = compute_affinity(X, K=20)
            affinities.append(W)

        # 2. SNF 网络融合
        print("   - 正在进行相似性网络迭代融合...")
        fused_sim = snf_fusion(affinities, t=20)

        # 3. 谱聚类
        print("   - 正在执行谱聚类划分亚型...")
        clustering = SpectralClustering(
            n_clusters=n_clusters, affinity='precomputed', random_state=42, n_init=10
        )
        labels = clustering.fit_predict(fused_sim)

        # 4. 保存为与 DEG 工具完美兼容的格式
        result_df = pd.DataFrame({
            "Sample_ID": sample_ids,
            "Subtype": [f"Subtype_{l + 1}" for l in labels]
        })
        labels_path = os.path.join(output_dir, f"snf_cluster_labels_k{n_clusters}.csv")
        result_df.to_csv(labels_path, index=False)

        return (f"✅ SNF 融合聚类成功！\n"
                f"聚类名单已保存至：'{labels_path}'\n"
                f"请立即使用该路径作为 labels_path，传给 DEG 差异分析工具寻找标志基因。")

    except Exception as e:
        return f"⚠️ SNF 聚类执行发生错误: {str(e)}"