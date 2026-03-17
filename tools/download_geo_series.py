#!/usr/bin/env python3
import argparse
import os
import sys
import urllib.request
from urllib.parse import urljoin

GEO_ROOT = "https://www.ncbi.nlm.nih.gov/geo/download/?acc="
FTP_ROOT = "https://ftp.ncbi.nlm.nih.gov/geo/series/"


def geo_ftp_series_dir(gse: str) -> str:
    # GEO uses GSEnnn folders (GSE000, GSE001, ...)
    prefix = gse[:-3]
    return f"{FTP_ROOT}{prefix}nnn/{gse}/"


def download(url: str, dest: str):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest):
        return "exists"
    try:
        urllib.request.urlretrieve(url, dest)
        return "ok"
    except Exception as e:
        return f"error: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gse", help="GEO Series accession, e.g. GSE57162")
    ap.add_argument("--out", default="/Volumes/mac-disk/PythonProject/Tumor_Subtype_Agent/data", help="output directory")
    args = ap.parse_args()

    gse = args.gse.strip()
    out_dir = os.path.abspath(args.out)

    # 1) Series Matrix via GEO download endpoint
    matrix_url = f"{GEO_ROOT}{gse}&format=file&file={gse}_series_matrix.txt.gz"
    matrix_dest = os.path.join(out_dir, f"{gse}_series_matrix.txt.gz")
    print(f"Downloading series matrix: {matrix_url}")
    print(download(matrix_url, matrix_dest))

    # 2) RAW supplementary tar from FTP
    series_dir = geo_ftp_series_dir(gse)
    raw_url = urljoin(series_dir, "suppl/") + f"{gse}_RAW.tar"
    raw_dest = os.path.join(out_dir, f"{gse}_RAW.tar")
    print(f"Downloading RAW tar: {raw_url}")
    print(download(raw_url, raw_dest))

    # 3) SOFT family (optional)
    soft_url = urljoin(series_dir, "soft/") + f"{gse}_family.soft.gz"
    soft_dest = os.path.join(out_dir, f"{gse}_family.soft.gz")
    print(f"Downloading SOFT: {soft_url}")
    print(download(soft_url, soft_dest))


if __name__ == "__main__":
    main()
