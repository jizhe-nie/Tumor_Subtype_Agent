import os
from typing import List
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from langchain_core.tools import tool
from tools.tool_utils import resolve_output_dir


def _build_ae_dims(input_dim: int, latent_dim: int) -> List[int]:
    if input_dim >= 1000:
        return [input_dim, 500, 200, latent_dim]
    if input_dim >= 200:
        return [input_dim, 128, 64, latent_dim]
    return [input_dim, 64, latent_dim]


@tool
def idec_tool(
    data_path: str,
    n_clusters: int,
    latent_dim: int = 10,
    pretrain_epochs: int = 50,
    finetune_epochs: int = 50,
    batch_size: int = 256,
    learning_rate: float = 1e-3,
    update_interval: int = 5,
) -> str:
    """
    IDEC (2017)：PyTorch 版简化实现（自编码器 + DEC 微调）。
    参数：
    - data_path: CSV 文件路径（行=样本，列=特征）
    - n_clusters: 期望亚型数量
    - latent_dim: 潜在维度
    - pretrain_epochs: 自编码器预训练轮数
    - finetune_epochs: IDEC 微调轮数
    - batch_size: 批大小
    - learning_rate: 学习率
    - update_interval: 更新 target distribution 的间隔（轮）
    返回：聚类标签文件路径
    """
    if not os.path.exists(data_path):
        return f"⚠️ 找不到数据文件：{data_path}"

    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    os.environ.setdefault("KMP_INIT_AT_FORK", "FALSE")
    os.environ.setdefault("KMP_USE_SHM", "FALSE")

    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset
    except Exception:
        return "⚠️ 未检测到 PyTorch。请先安装 torch，再重试。"

    df = pd.read_csv(data_path, index_col=0)
    X = df.values.astype(np.float32)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dims = _build_ae_dims(X.shape[1], latent_dim)

    class AutoEncoder(nn.Module):
        def __init__(self, dims):
            super().__init__()
            enc_layers = []
            for i in range(len(dims) - 1):
                enc_layers.append(nn.Linear(dims[i], dims[i + 1]))
                if i < len(dims) - 2:
                    enc_layers.append(nn.ReLU())
            self.encoder = nn.Sequential(*enc_layers)

            dec_dims = list(reversed(dims))
            dec_layers = []
            for i in range(len(dec_dims) - 1):
                dec_layers.append(nn.Linear(dec_dims[i], dec_dims[i + 1]))
                if i < len(dec_dims) - 2:
                    dec_layers.append(nn.ReLU())
            self.decoder = nn.Sequential(*dec_layers)

        def forward(self, x):
            z = self.encoder(x)
            x_hat = self.decoder(z)
            return z, x_hat

    ae = AutoEncoder(dims).to(device)
    optimizer = torch.optim.Adam(ae.parameters(), lr=learning_rate)
    mse = nn.MSELoss()

    dataset = TensorDataset(torch.from_numpy(X))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # 1) 预训练自编码器
    ae.train()
    for _ in range(pretrain_epochs):
        for (xb,) in loader:
            xb = xb.to(device)
            z, x_hat = ae(xb)
            loss = mse(x_hat, xb)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    # 2) 初始化聚类中心
    ae.eval()
    with torch.no_grad():
        z_all = []
        for (xb,) in DataLoader(dataset, batch_size=batch_size):
            z, _ = ae(xb.to(device))
            z_all.append(z.cpu().numpy())
        Z = np.concatenate(z_all, axis=0)

    kmeans = KMeans(n_clusters=n_clusters, n_init=20, random_state=42)
    y_pred = kmeans.fit_predict(Z)
    cluster_centers = torch.tensor(kmeans.cluster_centers_, dtype=torch.float32, device=device)

    # 3) DEC/IDEC 微调
    class IDECModel(nn.Module):
        def __init__(self, ae_model, centers):
            super().__init__()
            self.ae = ae_model
            self.cluster_centers = nn.Parameter(centers)

        def forward(self, x):
            z, x_hat = self.ae(x)
            q = 1.0 / (1.0 + torch.sum((z.unsqueeze(1) - self.cluster_centers) ** 2, dim=2))
            q = q / torch.sum(q, dim=1, keepdim=True)
            return z, x_hat, q

    model = IDECModel(ae, cluster_centers).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    def target_distribution(q):
        weight = q ** 2 / torch.sum(q, dim=0)
        return (weight.t() / torch.sum(weight, dim=1)).t()

    X_tensor = torch.from_numpy(X)
    for epoch in range(finetune_epochs):
        if epoch % update_interval == 0:
            model.eval()
            with torch.no_grad():
                q_all = []
                for (xb,) in DataLoader(dataset, batch_size=batch_size):
                    _, _, q = model(xb.to(device))
                    q_all.append(q.cpu())
                Q = torch.cat(q_all, dim=0)
                P = target_distribution(Q)
            model.train()

        for i, (xb,) in enumerate(loader):
            xb = xb.to(device)
            z, x_hat, q = model(xb)
            idx_start = i * batch_size
            idx_end = min((i + 1) * batch_size, X_tensor.shape[0])
            p_batch = P[idx_start:idx_end].to(device)
            kl_loss = torch.sum(p_batch * torch.log((p_batch + 1e-10) / (q + 1e-10)), dim=1).mean()
            recon_loss = mse(x_hat, xb)
            loss = kl_loss + recon_loss
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    # 4) 最终标签
    model.eval()
    with torch.no_grad():
        q_all = []
        for (xb,) in DataLoader(dataset, batch_size=batch_size):
            _, _, q = model(xb.to(device))
            q_all.append(q.cpu().numpy())
    Q = np.vstack(q_all)
    labels = Q.argmax(axis=1) + 1

    output_dir = resolve_output_dir([data_path], "IDEC")
    labels_path = os.path.join(output_dir, f"idec_labels_k{n_clusters}.csv")
    result_df = pd.DataFrame({
        "Sample_ID": df.index.tolist(),
        "Subtype": [f"Subtype_{l}" for l in labels],
    })
    result_df.to_csv(labels_path, index=False)

    return (f"✅ IDEC 聚类完成！\n"
            f"标签已保存至：'{labels_path}'\n"
            f"设备：{device}")
