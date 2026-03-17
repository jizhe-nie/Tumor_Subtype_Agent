#!/usr/bin/env python3
import argparse
import os
import sys
import gzip
import io
import tarfile
import bz2
import urllib.request
from urllib.error import HTTPError
import pandas as pd

DATA_ROOT_DEFAULT = "/Volumes/mac-disk/PythonProject/Tumor_Subtype_Agent/data"
FTP_ROOT = "https://ftp.ncbi.nlm.nih.gov/geo/series/"
GEO_DOWNLOAD = "https://www.ncbi.nlm.nih.gov/geo/download/?acc={gse}&format=file&file={gse}_series_matrix.txt.gz"

# METABRIC (processed) from Zenodo
METABRIC_TSV_URL = "https://zenodo.org/records/18272235/files/METABRIC.tsv.gz?download=1"
METABRIC_META_URL = "https://zenodo.org/records/18272235/files/METABRIC_metadata.tsv?download=1"

# CCLE expression (DepMap 18Q3 RNAseq RPKM) via public VAEN mirror
CCLE_GCT_URL = "https://bioinfo.uth.edu/VAEN/DATA/CCLE/CCLE_DepMap_18q3_RNAseq_RPKM_20180718.gct"


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def download(url: str, dest: str):
    ensure_dir(os.path.dirname(dest))
    if os.path.exists(dest):
        return "exists"
    try:
        urllib.request.urlretrieve(url, dest)
        return "ok"
    except Exception as e:
        return f"error: {e}"


def geo_series_dir(gse: str) -> str:
    prefix = gse[:-3]
    return f"{FTP_ROOT}{prefix}nnn/{gse}/"


def try_download_geo_matrix(gse: str, raw_dir: str):
    filename = f"{gse}_series_matrix.txt.gz"
    dest = os.path.join(raw_dir, filename)

    # 1) main GEO download endpoint
    url = GEO_DOWNLOAD.format(gse=gse)
    res = download(url, dest)
    if res == "ok" or res == "exists":
        return dest

    # 2) FTP matrix path
    ftp_url = geo_series_dir(gse) + f"matrix/{filename}"
    res2 = download(ftp_url, dest)
    if res2 == "ok" or res2 == "exists":
        return dest

    return None


def download_geo_soft(gse: str, raw_dir: str):
    filename = f"{gse}_family.soft.gz"
    dest = os.path.join(raw_dir, filename)
    url = geo_series_dir(gse) + f"soft/{filename}"
    res = download(url, dest)
    if res == "ok" or res == "exists":
        return dest
    return None


def download_geo_raw(gse: str, raw_dir: str):
    filename = f"{gse}_RAW.tar"
    dest = os.path.join(raw_dir, filename)
    url = geo_series_dir(gse) + f"suppl/{filename}"
    res = download(url, dest)
    if res == "ok" or res == "exists":
        return dest
    return None


def parse_series_matrix(gz_path: str, out_csv: str):
    with gzip.open(gz_path, "rt") as f:
        in_table = False
        table_lines = []
        for line in f:
            if line.startswith("!series_matrix_table_begin"):
                in_table = True
                continue
            if line.startswith("!series_matrix_table_end"):
                break
            if in_table:
                table_lines.append(line)
    if not table_lines:
        raise RuntimeError("no table found in series matrix")

    df = pd.read_csv(io.StringIO("".join(table_lines)), sep="\t", index_col=0)
    df.to_csv(out_csv)


def parse_soft_with_geoparse(soft_path: str, out_csv: str):
    try:
        import GEOparse
    except Exception as e:
        raise RuntimeError(f"GEOparse not installed: {e}")

    gse = GEOparse.get_GEO(filepath=soft_path, silent=True)
    # Build matrix using VALUE (or first numeric column)
    sample_tables = {}
    for gsm_name, gsm in gse.gsms.items():
        table = gsm.table
        if "VALUE" in table.columns:
            col = "VALUE"
        else:
            # pick first non-ID_REF column
            candidate_cols = [c for c in table.columns if c != "ID_REF"]
            if not candidate_cols:
                continue
            col = candidate_cols[0]
        sample_tables[gsm_name] = table.set_index("ID_REF")[col]

    if not sample_tables:
        raise RuntimeError("no usable sample tables found in SOFT")
    df = pd.DataFrame(sample_tables)
    df.to_csv(out_csv)


def parse_gse65525_raw(raw_tar: str, out_csv: str):
    # Aggregate per-sample scRNA matrices to sample-level means
    samples = {}
    with tarfile.open(raw_tar, "r") as tar:
        members = [m for m in tar.getmembers() if m.name.endswith(".csv.bz2")]
        for m in members:
            f = tar.extractfile(m)
            data = bz2.decompress(f.read())
            df = pd.read_csv(io.BytesIO(data), header=None)
            genes = df.iloc[:, 0]
            values = df.iloc[:, 1:]
            mean_expr = values.mean(axis=1)
            sample_name = os.path.splitext(os.path.splitext(os.path.basename(m.name))[0])[0]
            samples[sample_name] = pd.Series(mean_expr.values, index=genes.values)

    if not samples:
        raise RuntimeError("no sample matrices found in RAW tar")
    matrix = pd.DataFrame(samples)
    matrix.to_csv(out_csv)


def build_gse65525_cells(raw_tar: str, out_csv: str, max_cells: int = 2000, seed: int = 42):
    # Build a cells x genes matrix with downsampling to keep size manageable
    import random
    rng = random.Random(seed)
    members = []
    with tarfile.open(raw_tar, "r") as tar:
        members = [m for m in tar.getmembers() if m.name.endswith(".csv.bz2")]

    # First pass: count cells per file
    counts = []
    for m in members:
        with tarfile.open(raw_tar, "r") as tar:
            f = tar.extractfile(m)
            data = bz2.decompress(f.read())
            df_head = pd.read_csv(io.BytesIO(data), header=None, nrows=1)
            n_cells = df_head.shape[1] - 1
            counts.append(n_cells)

    total_cells = sum(counts)
    if total_cells == 0:
        raise RuntimeError("no cells found in RAW tar")

    # Allocate sample sizes per file
    alloc = []
    remaining = max_cells
    for n in counts:
        k = max(1, int(round(max_cells * n / total_cells)))
        alloc.append(k)
        remaining -= k
    # Adjust to exact max_cells
    i = 0
    while remaining > 0:
        alloc[i % len(alloc)] += 1
        remaining -= 1
        i += 1

    frames = []
    for m, n_cells, k in zip(members, counts, alloc):
        with tarfile.open(raw_tar, "r") as tar:
            f = tar.extractfile(m)
            data = bz2.decompress(f.read())
            # pick k columns from 1..n_cells
            cols = list(range(1, n_cells + 1))
            if k < n_cells:
                cols = rng.sample(cols, k)
            usecols = [0] + cols
            df = pd.read_csv(io.BytesIO(data), header=None, usecols=usecols)
            genes = df.iloc[:, 0].values
            values = df.iloc[:, 1:].to_numpy().T
            sample_name = os.path.splitext(os.path.splitext(os.path.basename(m.name))[0])[0]
            cell_ids = [f"{sample_name}_cell{i}" for i in range(values.shape[0])]
            frames.append(pd.DataFrame(values, index=cell_ids, columns=genes))

    cells_df = pd.concat(frames, axis=0)
    cells_df.to_csv(out_csv)

def convert_matrix_to_samples_rows(matrix_csv: str, out_csv: str):
    df = pd.read_csv(matrix_csv, index_col=0)
    # matrix is probes/genes x samples -> transpose
    df_t = df.T
    df_t.to_csv(out_csv)


def prepare_geo(gse_list, data_root):
    raw_dir = os.path.join(data_root, "geo_raw")
    proc_dir = os.path.join(data_root, "geo_processed")
    ensure_dir(raw_dir)
    ensure_dir(proc_dir)

    for gse in gse_list:
        print(f"== {gse} ==")
        matrix_path = try_download_geo_matrix(gse, raw_dir)
        if matrix_path:
            out_matrix = os.path.join(proc_dir, f"{gse}_matrix.csv")
            out_samples = os.path.join(proc_dir, f"{gse}_samples.csv")
            parse_series_matrix(matrix_path, out_matrix)
            convert_matrix_to_samples_rows(out_matrix, out_samples)
            print(f"matrix -> {out_matrix}")
            print(f"samples -> {out_samples}")
            continue

        soft_path = download_geo_soft(gse, raw_dir)
        if soft_path:
            out_matrix = os.path.join(proc_dir, f"{gse}_matrix.csv")
            out_samples = os.path.join(proc_dir, f"{gse}_samples.csv")
            try:
                parse_soft_with_geoparse(soft_path, out_matrix)
                convert_matrix_to_samples_rows(out_matrix, out_samples)
                print(f"soft -> {out_matrix}")
                print(f"samples -> {out_samples}")
                continue
            except Exception:
                pass

        # Fallback for scRNA-seq style datasets (e.g., GSE65525)
        raw_tar = download_geo_raw(gse, raw_dir)
        if raw_tar and gse == "GSE65525":
            out_matrix = os.path.join(proc_dir, f"{gse}_matrix.csv")
            out_samples = os.path.join(proc_dir, f"{gse}_samples.csv")
            parse_gse65525_raw(raw_tar, out_matrix)
            convert_matrix_to_samples_rows(out_matrix, out_samples)
            print(f"raw -> {out_matrix}")
            print(f"samples -> {out_samples}")
            continue

        print(f"WARNING: no matrix/soft/raw parse for {gse}")


def prepare_metabric(data_root):
    met_dir = os.path.join(data_root, "external", "metabric")
    ensure_dir(met_dir)
    tsv_path = os.path.join(met_dir, "METABRIC.tsv.gz")
    meta_path = os.path.join(met_dir, "METABRIC_metadata.tsv")
    download(METABRIC_TSV_URL, tsv_path)
    download(METABRIC_META_URL, meta_path)

    # convert expression to samples x genes
    df = pd.read_csv(tsv_path, sep="\t")
    # assume first column is gene id
    gene_col = df.columns[0]
    df = df.set_index(gene_col)
    out_matrix = os.path.join(met_dir, "METABRIC_matrix.csv")
    df.to_csv(out_matrix)
    out_samples = os.path.join(met_dir, "METABRIC_samples.csv")
    df.T.to_csv(out_samples)


def prepare_ccle(data_root):
    ccle_dir = os.path.join(data_root, "external", "ccle")
    ensure_dir(ccle_dir)
    ccle_path = os.path.join(ccle_dir, "CCLE_DepMap_18q3_RNAseq_RPKM_20180718.gct")
    download(CCLE_GCT_URL, ccle_path)

    # validate download
    if not os.path.exists(ccle_path) or os.path.getsize(ccle_path) < 1024:
        raise RuntimeError("CCLE download failed or file too small")
    with open(ccle_path, "rb") as f:
        head = f.read(8)
        if head.startswith(b"<"):
            raise RuntimeError("CCLE download returned HTML (likely blocked)")

    # Parse GCT to samples x genes
    df = pd.read_csv(ccle_path, sep="\t", skiprows=2)
    if "Name" in df.columns:
        df = df.set_index("Name")
    if "Description" in df.columns:
        df = df.drop(columns=["Description"])
    df.to_csv(os.path.join(ccle_dir, "CCLE_expression_matrix.csv"))
    df.T.to_csv(os.path.join(ccle_dir, "CCLE_expression_samples.csv"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=DATA_ROOT_DEFAULT)
    ap.add_argument("--geo", nargs="*", default=["GSE57162","GSE66354","GSE85217","GSE94601","GSE65525"], help="GSE accessions")
    ap.add_argument("--skip-geo", action="store_true")
    ap.add_argument("--skip-metabric", action="store_true")
    ap.add_argument("--skip-ccle", action="store_true")
    ap.add_argument("--make-gse65525-cells", action="store_true", help="build cells x genes matrix from GSE65525 RAW")
    ap.add_argument("--max-cells", type=int, default=2000)
    args = ap.parse_args()

    if not args.skip_geo:
        prepare_geo(args.geo, args.data_root)
    if args.make_gse65525_cells:
        raw_tar = os.path.join(args.data_root, "geo_raw", "GSE65525_RAW.tar")
        if os.path.exists(raw_tar):
            out_cells = os.path.join(args.data_root, "geo_processed", "GSE65525_cells.csv")
            build_gse65525_cells(raw_tar, out_cells, max_cells=args.max_cells)
            print(f"cells -> {out_cells}")
    if not args.skip_metabric:
        prepare_metabric(args.data_root)
    if not args.skip_ccle:
        prepare_ccle(args.data_root)

    print("Done")


if __name__ == "__main__":
    main()
