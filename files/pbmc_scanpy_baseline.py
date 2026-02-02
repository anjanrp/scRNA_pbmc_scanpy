import os
import argparse
import numpy as np
import pandas as pd
import scanpy as sc
import matplotlib.pyplot as plt


def ensure_dirs(outdir: str) -> tuple[str, str]:
    figdir = os.path.join(outdir, "figures")
    tabdir = os.path.join(outdir, "tables")
    os.makedirs(figdir, exist_ok=True)
    os.makedirs(tabdir, exist_ok=True)
    return figdir, tabdir


def savefig(path: str, dpi: int = 150) -> None:
    plt.savefig(path, bbox_inches="tight", dpi=dpi)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="PBMC3k Scanpy baseline pipeline.")
    parser.add_argument("--outdir", type=str, default="outputs", help="Output directory (default: outputs)")
    parser.add_argument("--min_genes", type=int, default=200, help="Min genes per cell (default: 200)")
    parser.add_argument("--min_cells", type=int, default=3, help="Min cells per gene (default: 3)")
    parser.add_argument("--max_pct_mito", type=float, default=10.0, help="Max percent mitochondrial counts (default: 10.0)")
    parser.add_argument("--n_top_hvgs", type=int, default=2000, help="Number of HVGs (default: 2000)")
    parser.add_argument("--n_neighbors", type=int, default=10, help="Neighbors for graph (default: 10)")
    parser.add_argument("--n_pcs", type=int, default=30, help="PCs to use for neighbors (default: 30)")
    parser.add_argument("--leiden_resolution", type=float, default=0.6, help="Leiden resolution (default: 0.6)")
    parser.add_argument("--dpi", type=int, default=150, help="Figure DPI (default: 150)")
    args = parser.parse_args()

    figdir, tabdir = ensure_dirs(args.outdir)

    # Scanpy settings
    sc.settings.verbosity = 2
    sc.settings.set_figure_params(dpi=args.dpi)
    # Make sure plots don't try to show in non-interactive runs
    sc.settings.autoshow = False

    # -------------------
    # Load dataset
    # -------------------
    print("Loading PBMC3k dataset...")
    adata = sc.datasets.pbmc3k()
    adata.var_names_make_unique()

    raw_cells, raw_genes = adata.n_obs, adata.n_vars
    print(f"Raw shape (cells x genes): ({raw_cells}, {raw_genes})")

    # -------------------
    # QC metrics
    # -------------------
    adata.var["mt"] = adata.var_names.str.upper().str.startswith("MT-")
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True)

    # QC plots (before)
    sc.pl.violin(
        adata,
        ["n_genes_by_counts", "total_counts", "pct_counts_mt"],
        jitter=0.4,
        multi_panel=True,
        show=False,
    )
    savefig(os.path.join(figdir, "qc_violin_before.png"), dpi=args.dpi)

    sc.pl.scatter(adata, x="total_counts", y="pct_counts_mt", show=False)
    savefig(os.path.join(figdir, "qc_scatter_counts_vs_mt_before.png"), dpi=args.dpi)

    sc.pl.scatter(adata, x="total_counts", y="n_genes_by_counts", show=False)
    savefig(os.path.join(figdir, "qc_scatter_counts_vs_genes_before.png"), dpi=args.dpi)

    # -------------------
    # Filter cells/genes
    # -------------------
    sc.pp.filter_cells(adata, min_genes=args.min_genes)
    sc.pp.filter_genes(adata, min_cells=args.min_cells)

    # Filter high mito
    adata = adata[adata.obs["pct_counts_mt"] < args.max_pct_mito, :].copy()

    qc_cells, qc_genes = adata.n_obs, adata.n_vars
    print(f"After QC filtering shape: ({qc_cells}, {qc_genes})")

    # QC plots (after)
    sc.pl.violin(
        adata,
        ["n_genes_by_counts", "total_counts", "pct_counts_mt"],
        jitter=0.4,
        multi_panel=True,
        show=False,
    )
    savefig(os.path.join(figdir, "qc_violin_after.png"), dpi=args.dpi)

    # QC summary table (useful for resume metrics)
    qc_summary = {
        "cells_raw": int(raw_cells),
        "genes_raw": int(raw_genes),
        "cells_retained": int(qc_cells),
        "genes_retained": int(qc_genes),
        "median_genes_per_cell": float(np.median(adata.obs["n_genes_by_counts"])),
        "median_umis_per_cell": float(np.median(adata.obs["total_counts"])),
        "median_pct_mito": float(np.median(adata.obs["pct_counts_mt"])),
        "min_genes_filter": int(args.min_genes),
        "min_cells_filter": int(args.min_cells),
        "max_pct_mito_filter": float(args.max_pct_mito),
    }
    qc_df = pd.DataFrame([qc_summary])
    qc_path = os.path.join(tabdir, "qc_summary.csv")
    qc_df.to_csv(qc_path, index=False)
    print("\nQC summary saved:", qc_path)
    print(qc_df.to_string(index=False))

    # -------------------
    # Normalize + log transform
    # -------------------
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    # HVGs
    sc.pp.highly_variable_genes(adata, n_top_genes=args.n_top_hvgs, flavor="seurat_v3")
    sc.pl.highly_variable_genes(adata, show=False)
    savefig(os.path.join(figdir, "hvgs.png"), dpi=args.dpi)

    # Keep HVGs only
    adata = adata[:, adata.var["highly_variable"]].copy()
    print(f"After HVG selection shape: ({adata.n_obs}, {adata.n_vars})")

    # Scale + PCA
    sc.pp.scale(adata, max_value=10)
    sc.tl.pca(adata, svd_solver="arpack")
    sc.pl.pca_variance_ratio(adata, log=True, show=False)
    savefig(os.path.join(figdir, "pca_variance_ratio.png"), dpi=args.dpi)

    # -------------------
    # Neighbors + UMAP + Leiden
    # -------------------
    sc.pp.neighbors(adata, n_neighbors=args.n_neighbors, n_pcs=args.n_pcs)
    sc.tl.umap(adata)
    sc.tl.leiden(adata, resolution=args.leiden_resolution)

    num_clusters = int(adata.obs["leiden"].nunique())
    print(f"Leiden clusters: {num_clusters} (resolution={args.leiden_resolution})")

    sc.pl.umap(adata, color=["leiden"], legend_loc="on data", show=False)
    savefig(os.path.join(figdir, "umap_leiden.png"), dpi=args.dpi)

    # -------------------
    # Marker genes
    # -------------------
    sc.tl.rank_genes_groups(adata, groupby="leiden", method="wilcoxon")

    sc.pl.rank_genes_groups(adata, n_genes=15, sharey=False, show=False)
    savefig(os.path.join(figdir, "marker_genes_top15.png"), dpi=args.dpi)

    markers = sc.get.rank_genes_groups_df(adata, group=None)
    markers_all_path = os.path.join(tabdir, "marker_genes_all_clusters.csv")
    markers.to_csv(markers_all_path, index=False)

    top15 = markers.groupby("group", sort=False).head(15)
    top15_path = os.path.join(tabdir, "marker_genes_top15_per_cluster.csv")
    top15.to_csv(top15_path, index=False)

    # Save key run summary
    run_summary = {
        "cells_retained": qc_cells,
        "genes_retained": qc_genes,
        "hvgs_used": int(adata.n_vars),
        "clusters": num_clusters,
        "leiden_resolution": args.leiden_resolution,
        "n_neighbors": args.n_neighbors,
        "n_pcs": args.n_pcs,
    }
    pd.DataFrame([run_summary]).to_csv(os.path.join(tabdir, "run_summary.csv"), index=False)

    print("\nDone.")
    print(f"Figures: {figdir}")
    print(f"Tables : {tabdir}")
    print("Key tables:", markers_all_path, "and", top15_path)


if __name__ == "__main__":
    main()