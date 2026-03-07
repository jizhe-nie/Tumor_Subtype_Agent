import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import os
from langchain_core.tools import tool  # 🌟 引入 tool 装饰器


@tool
def pca_reduction_tool(data_path: str, n_components: int) -> str:
    """
    当你面临高维基因数据（如几百上千个基因），需要先进行特征降维时，请务必先调用此工具。
    参数：
    - data_path: 原始基因表达数据的 CSV 文件路径。
    - n_components: 目标维度（通常设定在 10 到 50 之间）。
    返回：降维后新生成的数据文件路径和解释率。
    """
    print(f"📉 [Tool调用] 正在对数据进行 PCA 降维: {data_path} (目标维度={n_components})...")

    if not os.path.exists(data_path):
        return f"执行失败：找不到数据文件 {data_path}，请检查路径。"

    try:
        df = pd.read_csv(data_path, index_col=0)
        if df.shape[1] <= n_components:
            return f"无需降维：原始数据的特征数 ({df.shape[1]}) 已经小于或等于目标维度 ({n_components})。"

        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df)

        pca = PCA(n_components=n_components, random_state=42)
        pca_data = pca.fit_transform(scaled_data)
        explained_variance = sum(pca.explained_variance_ratio_) * 100

        new_columns = [f"PC_{i + 1}" for i in range(n_components)]
        pca_df = pd.DataFrame(pca_data, index=df.index, columns=new_columns)

        dir_name = os.path.dirname(data_path)
        base_name = os.path.basename(data_path)
        new_file_path = os.path.join(dir_name, f"pca_{n_components}_{base_name}")
        pca_df.to_csv(new_file_path)

        result_msg = (
            f"✅ PCA 降维执行成功！\n"
            f"📊 维度变化: {df.shape[1]} 个特征 -> {n_components} 个主成分。\n"
            f"💡 信息保留度: 解释了原始数据 {explained_variance:.2f}% 的方差。\n"
            f"💾 降维后的新数据已保存至: '{new_file_path}' (请务必在后续聚类步骤中使用此新路径)。"
        )
        return result_msg
    except Exception as e:
        return f"执行降维过程中发生错误: {str(e)}"