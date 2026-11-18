# IEEE Manuscript Build

The manuscript source is:

- IEEEtran wrapper: `paper/IEEE_PAPER_DRAFT.tex`
- normalized manuscript body: `paper/IEEE_PAPER_BODY.md`
- citation registry: `paper/CITATION_REGISTRY.md`
- claim-evidence matrix: `PAPER_CLAIM_EVIDENCE_MATRIX.md`

## Local compilation

From the repository root:

```bash
python scripts/build_ieee_paper.py
cd paper
pdflatex -interaction=nonstopmode -halt-on-error IEEE_PAPER_DRAFT.tex
pdflatex -interaction=nonstopmode -halt-on-error IEEE_PAPER_DRAFT.tex
```

The build script converts the maintained Markdown body to `IEEE_PAPER_BODY.tex`, converts Markdown tables to IEEE column-contained `tabular` blocks, and then the IEEEtran wrapper compiles the generated body. No shell escape is required.

The source uses `IEEEtran` conference mode, which produces the standard IEEE two-column letter-size layout. The author metadata in the wrapper is intentionally a placeholder and must be replaced before submission.

## Citation control

The manuscript currently retains explicit IEEE citation numbers [1]–[13]. The permanent source identities are tracked by `CIT-001`–`CIT-010` in `paper/CITATION_REGISTRY.md`.

Before final submission:

1. Freeze the complete reference set.
2. Reconcile every [n] citation with the final IEEE bibliography numbering.
3. Replace placeholder author metadata.
4. Run the research harness.
5. Compile the full paper and inspect every table, equation, reference, and page break.
