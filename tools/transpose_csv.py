from typing import Any
import pandas as pd
from langchain_core.tools import tool

@tool
def transpose_csv(raw_data_path: str) -> str:
    """
    【专用转置工具】将输入CSV文件强制转置（行↔列互换），并保存为新文件。
    适用于组学数据格式对齐：如甲基化矩阵需从 CpG×样本 → 样本×CpG。
    
    参数:
        raw_data_path (str): 原始CSV文件路径。
    
    返回:
        str: 转置后CSV的绝对路径（格式为 '{raw_data_path}_transposed.csv'）。
    """
    df = pd.read_csv(raw_data_path, index_col=0)
    df_t = df.T
    output_path = f"{raw_data_path}_transposed.csv"
    df_t.to_csv(output_path)
    return output_path