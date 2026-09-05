"""Generate lightweight dataset documentation from the actual CSV outputs."""

from pathlib import Path
import pandas as pd

from config import DATA_DIR, CORE_DIR, DEMO_DIR

def write_manifest(dfs):
    lines = [
        "# Dataset Manifest",
        "",
        "Generated from the current CSV outputs.",
        "",
        "| File | Rows | Columns |",
        "|---|---:|---:|",
    ]
    for name, df in dfs.items():
        lines.append(f"| `{name}` | {len(df):,} | {len(df.columns)} |")
    (DATA_DIR / "DATASET_MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def write_profile(dfs):
    lines = ["# Data Profile", ""]
    for name, df in dfs.items():
        lines += [f"## `{name}`", "", f"- Rows: **{len(df):,}**",
                  f"- Columns: **{len(df.columns)}**", ""]
        for col in df.columns:
            lines.append(f"- `{col}`: {df[col].nunique(dropna=False):,} distinct values")
        lines.append("")
    (DATA_DIR / "DATA_PROFILE.md").write_text("\n".join(lines), encoding="utf-8")

def write_dictionary(dfs):
    lines = [
        "# ML Data Dictionary",
        "",
        "This file is generated from the actual dataset schema.",
        "",
    ]
    for name, df in dfs.items():
        lines += [f"## `{name}`", "", "| Column | Type | Nulls |", "|---|---|---:|"]
        for col in df.columns:
            lines.append(f"| `{col}` | `{df[col].dtype}` | {int(df[col].isna().sum()):,} |")
        lines.append("")
    (DATA_DIR / "ML_DATA_DICTIONARY.md").write_text("\n".join(lines), encoding="utf-8")

def main():
    core = {
        "core/merchants.csv": pd.read_csv(CORE_DIR / "merchants.csv"),
        "core/customers.csv": pd.read_csv(CORE_DIR / "customers.csv"),
        "core/transactions.csv": pd.read_csv(CORE_DIR / "transactions.csv"),
        "core/disputes.csv": pd.read_csv(CORE_DIR / "disputes.csv"),
        "core/evidence.csv": pd.read_csv(CORE_DIR / "evidence.csv"),
        "demo/demo_merchants.csv": pd.read_csv(DEMO_DIR / "demo_merchants.csv"),
    }
    write_manifest(core)
    write_profile(core)
    write_dictionary(core)
    print("Generated DATASET_MANIFEST.md, DATA_PROFILE.md and ML_DATA_DICTIONARY.md")

if __name__ == "__main__":
    main()
