import os
import datetime
from langchain_core.tools import tool


@tool
def generate_report_tool(report_title: str, report_content_md: str) -> str:
    """
    【核心工具】：报告实体化生成器
    当你的整个分析流水线（如数据清洗、聚类、差异分析）全部完成后，
    必须调用此工具，将你的最终医学解读与发现保存为实体文件，交付给用户。
    参数：
    - report_title: 报告的标题（例如 "TCGA-BRCA_多组学靶点分析报告"）。
    - report_content_md: 包含极其详细的分析过程、表格、标志基因列表及临床解释的完整 Markdown 格式长文本。
    返回：实体文件保存的绝对路径。
    """
    print(f"📝 [Tool调用] 正在排版并生成最终分析报告: {report_title}...")

    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(project_root, "output", "Final_Reports")
        os.makedirs(output_dir, exist_ok=True)

        # 处理文件名
        safe_title = report_title.replace(" ", "_").replace("/", "-")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{safe_title}_{timestamp}.md"
        file_path = os.path.join(output_dir, file_name)

        # 写入 Markdown 报告
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {report_title}\n\n")
            f.write(f"**生成时间:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(report_content_md)

        return f"✅ 实体报告生成成功！文件已保存至：'{file_path}'。请告诉用户可以使用 Markdown 阅读器或浏览器打开该文件，并使用 Ctrl+P 完美导出为 PDF 格式。"

    except Exception as e:
        return f"⚠️ 生成报告时发生错误: {str(e)}"