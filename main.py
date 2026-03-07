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


if __name__ == "__main__":
    # 确保 data 文件夹存在
    os.makedirs("data", exist_ok=True)

    # 生成测试数据集
    data_file = "data/dummy_tcga_expression.csv"
    if not os.path.exists(data_file):
        generate_dummy_tcga_data(data_file)
    else:
        print("测试数据已存在，准备进入下一步开发！")