import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
import os
from langchain_core.tools import tool


@tool
def plot_pca_clusters_tool(data_path: str, n_clusters: int) -> str:
    """
    当你需要将聚类结果“可视化”或“画散点图”时，请调用此工具。
    参数：
    - data_path: 降维后的数据文件路径（例如 PCA 生成的 csv）。
    - n_clusters: 聚类的亚型数量 (k)。
    返回：生成的图片保存路径。
    """
    print(f"🎨 [Tool调用] 正在生成聚类可视化 2D 散点图 (k={n_clusters})...")

    if not os.path.exists(data_path):
        return f"⚠️ 错误：找不到数据文件 '{data_path}'。"

    try:
        df = pd.read_csv(data_path, index_col=0)
        if df.shape[1] < 2:
            return "⚠️ 错误：数据特征维度小于 2，无法绘制 2D 散点图。"

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(df)
        df['Subtype'] = [f"Subtype_{i + 1}" for i in labels]

        plt.figure(figsize=(8, 6))
        sns.set_theme(style="whitegrid")
        col1, col2 = df.columns[0], df.columns[1]

        sns.scatterplot(data=df, x=col1, y=col2, hue='Subtype', palette='Set2', s=60, alpha=0.8)
        plt.title(f"Tumor Subtypes PCA Clustering (k={n_clusters})", fontsize=14)
        plt.tight_layout()

        # 🌟 核心升级：将输出重定向到项目的 output 文件夹
        # 获取项目的根目录 (tools 的上一级)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 获取当前数据所在的文件夹名字（比如 'tcga_brca_expr'）
        data_dir = os.path.dirname(os.path.abspath(data_path))
        dataset_folder_name = os.path.basename(data_dir)

        # 兜底机制：如果没在子文件夹里，就从文件名提取
        if dataset_folder_name == "data":
            file_name = os.path.basename(data_path)
            dataset_folder_name = file_name.replace("pca_", "").replace("clean_", "").split(".")[0]

        # 组装最终的 output 路径：ProjectRoot/output/DatasetName/
        output_dir = os.path.join(project_root, "output", dataset_folder_name)
        os.makedirs(output_dir, exist_ok=True)  # 自动创建 output 和子文件夹

        img_path = os.path.join(output_dir, f"cluster_plot_k{n_clusters}.png")
        plt.savefig(img_path, dpi=300)
        plt.close()

        return f"✅ 可视化成功！图片已分类保存至结果专属目录: '{img_path}'。"

    except Exception as e:
        return f"⚠️ 绘图时发生错误: {str(e)}"