import pandas as pd
import numpy as np
import os
from langchain_core.tools import tool


@tool
def data_preprocessing_tool(raw_data_path: str) -> str:
    """
    当你拿到一份【原始】的基因表达数据（未清洗的数据），在进行降维或聚类之前，必须先调用此工具。
    支持 .csv, .tsv, .txt 等多种格式。
    返回：清洗后生成的新文件路径和数据概况。
    """
    print(f"🧹 [Tool调用] 正在清洗和预处理原始数据: {raw_data_path}...")

    if not os.path.exists(raw_data_path):
        return f"⚠️ 错误：找不到原始数据文件 '{raw_data_path}'。请核对路径。"

    try:
        if raw_data_path.lower().endswith('.tsv') or raw_data_path.lower().endswith('.txt'):
            df = pd.read_csv(raw_data_path, index_col=0, sep='\t')
        else:
            df = pd.read_csv(raw_data_path, index_col=0)

        original_shape = df.shape
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        df = df.select_dtypes(include=[np.number])
        df = df.fillna(0)

        transposed = False
        if df.shape[0] > df.shape[1] * 2:
            df = df.T
            transposed = True

        # 🌟 核心升级：为数据集自动建立独立专属文件夹
        dir_name = os.path.dirname(raw_data_path)
        base_name = os.path.basename(raw_data_path)
        name_without_ext = os.path.splitext(base_name)[0]

        # 避免重复嵌套（如果已经在同名文件夹里了就不建了）
        if os.path.basename(dir_name) != name_without_ext:
            project_data_dir = os.path.join(dir_name, name_without_ext)
            os.makedirs(project_data_dir, exist_ok=True)
        else:
            project_data_dir = dir_name

        clean_file_path = os.path.join(project_data_dir, f"clean_{name_without_ext}.csv")
        df.to_csv(clean_file_path)

        msg = (
            f"✅ 数据清洗成功！\n"
            f"📊 原始数据形状: {original_shape[0]} 行, {original_shape[1]} 列。\n"
        )
        if transposed:
            msg += f"🔄 已自动执行【矩阵转置】。\n"
        msg += (
            f"✨ 清洗后数据形状: {df.shape[0]} x {df.shape[1]}。\n"
            f"💾 清洗后的数据已**归档至专属文件夹**: '{clean_file_path}'。请务必使用此新路径进行下一步计算。"
        )
        return msg

    except Exception as e:
        return f"⚠️ 数据清洗发生错误: {str(e)}"