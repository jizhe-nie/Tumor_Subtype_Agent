import pandas as pd
import numpy as np
import os


def generate_dummy_tcga_data(file_path, num_samples=150, num_genes=500):
    """
    生成一个模拟的肿瘤基因表达矩阵，用于在真实数据下载前测试代码。
    包含 3 个隐藏的亚型（这模拟了不同的肿瘤亚型特征）。
    """
    np.random.seed(42)  # 保证每次生成的数据一样

    print(f"开始生成模拟基因表达数据，样本数: {num_samples}, 基因数: {num_genes}...")

    # 模拟 3 个不同的肿瘤亚型分布
    cluster_1 = np.random.normal(loc=1.0, scale=0.5, size=(num_samples // 3, num_genes))
    cluster_2 = np.random.normal(loc=3.0, scale=0.5, size=(num_samples // 3, num_genes))
    cluster_3 = np.random.normal(loc=5.0, scale=0.5, size=(num_samples // 3, num_genes))

    # 合并数据
    data_matrix = np.vstack([cluster_1, cluster_2, cluster_3])

    # 创建特征名(基因名)和样本名
    genes = [f"Gene_{i + 1}" for i in range(num_genes)]
    samples = [f"Patient_{i + 1}" for i in range(num_samples)]

    # 转换为 DataFrame 并保存
    df = pd.DataFrame(data_matrix, index=samples, columns=genes)
    df.to_csv(file_path)
    print(f"数据已成功保存至: {file_path}")


# if __name__ == "__main__":
#     # 确保 data 文件夹存在
#     os.makedirs("data", exist_ok=True)
#
#     # 生成测试数据集
#     data_file = "data/dummy_tcga_expression.csv"
#     if not os.path.exists(data_file):
#         generate_dummy_tcga_data(data_file)
#     else:
#         print("测试数据已存在，准备进入下一步开发！")

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    # 我们生成一份“方向颠倒（行是基因，列是样本）”并且带有 NaN 的脏数据
    dirty_data_file = "data/raw_tcga_dirty.csv"

    print("正在生成模拟的 TCGA 原始脏数据...")
    np.random.seed(42)
    # 模拟 1000 个基因, 120 个样本
    raw_matrix = np.random.normal(loc=5.0, scale=2.0, size=(1000, 120))

    # 随机加入一些缺失值 NaN (模拟未检出)
    mask = np.random.choice([True, False], size=raw_matrix.shape, p=[0.05, 0.95])
    raw_matrix[mask] = np.nan

    # 生成 DataFrame：注意这里 index 是基因，columns 是样本（这是生信常见格式）
    genes = [f"Gene_{i + 1}" for i in range(1000)]
    samples = [f"Patient_{i + 1}" for i in range(120)]
    df_dirty = pd.DataFrame(raw_matrix, index=genes, columns=samples)

    df_dirty.to_csv(dirty_data_file)
    print(f"脏数据已生成并保存至: {dirty_data_file}")