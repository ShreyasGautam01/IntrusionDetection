# IEEE Manuscript Build

The manuscript source is:

- IEEEtran wrapper: `paper/IEEE_PAPER_DRAFT.tex`
- normalized manuscript body: `paper/IEEE_PAPER_BODY.md`
- citation registry: `paper/CITATION_REGISTRY.md`
- claim-evidence matrix: `PAPER_CLAIM_EVIDENCE_MATRIX.md`

## Local compilation

From the `paper/` directory:

```bash
pdflatex -shell-escape IEEE_PAPER_DRAFT.tex
pdflatex -shell-escape IEEE_PAPER_DRAFT.tex
```

The `-shell-escape` flag is required because the LaTeX markdown package imports the maintained Markdown body during compilation.

The source uses `IEEEtran` conference mode, which produces the standard IEEE two-column letter-size layout. The author metadata in the wrapper is intentionally a placeholder and must be replaced before submission.

## Citation control

The manuscript currently retains explicit IEEE citation numbers [1]–[10]. The permanent source identities are tracked by `CIT-001`–`CIT-010` in `paper/CITATION_REGISTRY.md`.

Before final submission:

1. Freeze the complete reference set.
2. Reconcile every [n] citation with the final IEEE bibliography numbering.
3. Replace placeholder author metadata.
4. Run the research harness.
5. Compile the full paper and inspect every table, equation, reference, and page break.
