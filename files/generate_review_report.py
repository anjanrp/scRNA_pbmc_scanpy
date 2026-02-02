#!/usr/bin/env python3
import os
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd


def df_to_md(df: pd.DataFrame, max_rows: int | None = None) -> str:
    """Convert dataframe to markdown table. Uses pandas' to_markdown if available."""
    if max_rows is not None:
        df = df.head(max_rows)
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_string(index=False)


def embed_image(md_lines: list[str], rel_path: str, title: str) -> None:
    md_lines.append(f"### {title}")
    md_lines.append("")
    md_lines.append(f"![{title}]({rel_path})")
    md_lines.append("")


def main():
    parser = argparse.ArgumentParser(description="Generate QC + clustering review report (MD + HTML).")
    parser.add_argument("--outdir", type=str, default="outputs", help="Output directory (default: outputs)")
    parser.add_argument("--top_marker_rows", type=int, default=60, help="Rows of marker table to show in report")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    figdir = outdir / "figures"
    tabdir = outdir / "tables"

    # Required artifacts from your pipeline
    qc_path = tabdir / "qc_summary.csv"
    run_path = tabdir / "run_summary.csv"
    markers_path = tabdir / "marker_genes_top15_per_cluster.csv"

    missing = [p for p in [qc_path, run_path, markers_path] if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required artifacts. Run pbmc_scanpy_baseline.py first.\n"
            + "\n".join([f"- {m}" for m in missing])
        )

    qc_df = pd.read_csv(qc_path)
    run_df = pd.read_csv(run_path)
    markers_df = pd.read_csv(markers_path)

    # Choose the plots to bundle (these match your filenames)
    plot_files = [
        ("figures/qc_violin_before.png", "QC violin (before filtering)"),
        ("figures/qc_scatter_counts_vs_mt_before.png", "QC scatter: counts vs % mito (before)"),
        ("figures/qc_scatter_counts_vs_genes_before.png", "QC scatter: counts vs genes (before)"),
        ("figures/qc_violin_after.png", "QC violin (after filtering)"),
        ("figures/hvgs.png", "Highly variable genes (HVGs)"),
        ("figures/pca_variance_ratio.png", "PCA variance ratio"),
        ("figures/umap_leiden.png", "UMAP with Leiden clusters"),
        ("figures/marker_genes_top15.png", "Top marker genes (per cluster)"),
    ]

    # Filter plot list to only those that exist (robust)
    plot_files = [(p, t) for (p, t) in plot_files if (outdir / p).exists()]

    # Build Markdown report
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md = []
    md.append("# PBMC3k QC + Clustering Review Report")
    md.append("")
    md.append(f"**Generated:** {ts}")
    md.append(f"**Artifacts:** `{outdir}`")
    md.append("")

    md.append("## 1) Run Summary")
    md.append("")
    md.append(df_to_md(run_df))
    md.append("")

    md.append("## 2) QC Summary")
    md.append("")
    md.append(df_to_md(qc_df))
    md.append("")

    md.append("## 3) Key Visualizations")
    md.append("")
    for rel_path, title in plot_files:
        embed_image(md, rel_path, title)

    md.append("## 4) Top Marker Genes per Cluster")
    md.append("")
    md.append(df_to_md(markers_df, max_rows=args.top_marker_rows))
    md.append("")
    md.append(f"Full table: `{markers_path}`")
    md.append("")

    md.append("## 5) Output Files")
    md.append("")
    md.append("- Figures: `outputs/figures/`")
    md.append("- Tables: `outputs/tables/`")
    md.append("- Report (Markdown): `outputs/report.md`")
    md.append("- Report (HTML): `outputs/report.html`")
    md.append("")

    report_md = outdir / "report.md"
    report_md.write_text("\n".join(md), encoding="utf-8")
    print("[OK] Wrote:", report_md)

    # Create HTML (needs `markdown` package)
    report_html = outdir / "report.html"
    try:
        import markdown  # pip install markdown
        md_text = report_md.read_text(encoding="utf-8")
        html_body = markdown.markdown(md_text, extensions=["tables"])
        html_doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>PBMC3k QC + Clustering Review Report</title>
<style>
  body {{ font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial,sans-serif; margin: 24px; }}
  table {{ border-collapse: collapse; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 10px; }}
  th {{ background: #f6f6f6; }}
  img {{ max-width: 100%; height: auto; border: 1px solid #eee; padding: 6px; margin: 6px 0; }}
  code {{ background: #f6f6f6; padding: 2px 4px; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
        report_html.write_text(html_doc, encoding="utf-8")
        print("[OK] Wrote:", report_html)
    except Exception as e:
        print("[WARN] HTML not generated. Install dependency: pip install markdown")
        print("       Error:", str(e))


if __name__ == "__main__":
    main()
