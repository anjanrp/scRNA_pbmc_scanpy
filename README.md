# scRNA_pbmc_scanpy

# Single-cell RNA-seq QC + Clustering Baseline (Scanpy, PBMC3k)

A small, reproducible baseline pipeline for single-cell RNA-seq analysis using **Scanpy** on the public **PBMC3k** dataset.

This project runs a standard workflow:  
**QC → filtering → normalization → HVGs → PCA → UMAP → Leiden clustering → marker genes**, and exports **report-ready figures** and **CSV tables** as traceable artifacts.

---

## What this project produces

### Figures (`outputs/figures/`)
- `qc_violin_before.png` — QC violin plot (genes/cell, UMIs/cell, % mito) *before* filtering  
- `qc_scatter_counts_vs_genes_before.png` — total counts vs genes per cell (before)  
- `qc_scatter_counts_vs_mt_before.png` — total counts vs % mito (before)  
- `qc_violin_after.png` — QC violin plot *after* filtering  
- `hvgs.png` — highly variable genes selection plot  
- `pca_variance_ratio.png` — PCA variance (scree) plot  
- `umap_leiden.png` — UMAP embedding colored by Leiden clusters  
- `marker_genes_top15.png` — top marker genes per cluster plot

### Tables (`outputs/tables/`)
- `qc_summary.csv` — QC summary (cells/genes retained + median QC metrics)  
- `run_summary.csv` — run settings + high-level outputs (clusters, HVGs, etc.)  
- `marker_genes_all_clusters.csv` — ranked marker genes for all clusters  
- `marker_genes_top15_per_cluster.csv` — top 15 markers per cluster (compact table)

---

## Key results (this run)

From the PBMC3k run captured in the exported summaries:

- Raw: **2700 cells**, **32,738 genes**
- Post-QC: **2694 cells**, **13,714 genes**
- Median QC metrics (post-QC): **817 genes/cell**, **2200 UMIs/cell**, **2.03% mitochondrial**
- HVGs: **2000**
- Clusters: **9** (Leiden resolution **0.6**)

> Note: Small changes to filtering thresholds or Leiden resolution can change the number of clusters.

---

## Repo structure (suggested)

```text
.
├── pbmc_scanpy_baseline.py          # main script (or notebooks/pbmc_scanpy_baseline.py)
├── environment.yml                  # conda env export (recommended)
├── outputs/
│   ├── figures/
│   └── tables/
└── README.md
```


## Setup (Conda)

### 1) Create and activate the environment

```bash
conda create -n scrna-scanpy -c conda-forge python=3.10 scanpy anndata leidenalg python-igraph matplotlib pandas numpy scipy -y
conda activate scrna-scanpy
```


### 2) Verify Scanpy import
```bash
python -c "import scanpy as sc; print('scanpy version:', sc.__version__)"
```

### Run the pipeline
From the project root:
```bash 
python pbmc_scanpy_baseline.py
```

After the run, check outputs:
```bash 
ls outputs/figures
ls outputs/tables
```

### Parameters
```bash 
python pbmc_scanpy_baseline.py \
  --min_genes 200 \
  --min_cells 3 \
  --max_pct_mito 10 \
  --n_top_hvgs 2000 \
  --leiden_resolution 0.6
``` 
### Reproducibility notes

All outputs are saved to disk (figures + CSV tables), making runs easy to review and share.

### HTML report 
[Open HTML report](https://anjanrp.github.io/scRNA_pbmc_scanpy/)


