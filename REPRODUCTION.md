# Reproduction and environment notes

The repository declares its environment in `pyproject.toml` and `uv.lock`:

- Python `>=3.14,<3.15`
- `uv==0.11.19`
- NumPy `2.5.2`
- pandas `3.0.6`
- scikit-learn `1.9.1`

For a new checkout with the required Python and uv versions installed, the locked dependency environment can be prepared with:

```powershell
uv sync --locked
```

This command was not run as part of archiving the completed experiment. The existing experiment environment and lockfile are preserved unchanged.

## Data and completed results

Raw datasets and large generated arrays are intentionally excluded from Git. Reproducing the post-transfer analysis requires the local data/artifact files referenced by the committed transfer manifests and evaluation reports. The analysis runner is `scripts/run_complete_transfer_analysis.py`; its documented `--resume` mode skips phases recorded complete and validates the transfer manifests before evaluation. Running that script is a new analysis execution that reads target labels for offline evaluation. Do not run it merely to inspect the archived results; use the committed CSV, JSON, Markdown, figure, and hash records under `reports/nf_v3_audit/`.

No transfer scoring, RF fitting, distance computation, or label-derived training was performed while preparing this archive.
