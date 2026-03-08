import pandas as pd
import numpy as np
import os


def generate_mock_methylation():
    # 读取之前清洗好的基因表达数据，获取真实的患者 ID
    expr_path = "data/tcga_brca_expr/clean_tcga_brca_expr.csv"

    if not os.path.exists(expr_path):
        print(f"❌ 找不到清洗后的表达数据：{expr_path}")
        print("请确认你之前的数据清洗步骤已经成功生成了该文件。")
        return

    print("正在读取表达数据以对齐患者样本 ID...")
    expr_df = pd.read_csv(expr_path, index_col=0)
    patient_ids = expr_df.index

    print(f"成功获取 {len(patient_ids)} 个患者样本。正在生成匹配的 DNA 甲基化特征...")

    # 模拟 DNA 甲基化数据 (Beta values 通常在 0 到 1 之间)
    np.random.seed(42)
    # 模拟 500 个高变甲基化探针位点
    meth_data = np.random.beta(a=2, b=5, size=(len(patient_ids), 500))

    # 构建 DataFrame 并保存
    meth_df = pd.DataFrame(meth_data, index=patient_ids, columns=[f"cg_probe_{i + 1}" for i in range(500)])

    meth_path = "data/tcga_brca_meth.csv"
    meth_df.to_csv(meth_path)
    print(f"✅ 成功生成匹配的模拟 DNA 甲基化数据！已保存至：{meth_path}")


if __name__ == "__main__":
    generate_mock_methylation()