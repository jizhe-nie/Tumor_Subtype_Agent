import os


def resolve_output_dir(data_paths, method_name: str):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_name = os.path.basename(os.path.dirname(os.path.abspath(data_paths[0])))
    if dataset_name == "data":
        dataset_name = os.path.basename(data_paths[0]).split(".")[0]
    output_dir = os.path.join(project_root, "output", dataset_name, method_name)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def safe_path(path: str) -> str:
    return os.path.abspath(path).replace("\\", "/")
