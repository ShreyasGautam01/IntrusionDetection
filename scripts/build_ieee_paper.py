#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
BODY_MD = PAPER / "IEEE_PAPER_BODY.md"
BODY_TEX = PAPER / "IEEE_PAPER_BODY.tex"
PANDOC_MD = PAPER / "_IEEE_PAPER_BODY_PANDOC.md"

def main() -> None:
    if not BODY_MD.exists():
        raise SystemExit(f"Missing manuscript body: {BODY_MD}")

    source = BODY_MD.read_text(encoding="utf-8")
    source = source.replace("\\[", "$$").replace("\\]", "$$")
    PANDOC_MD.write_text(source, encoding="utf-8")

    subprocess.run(
        [
            "pandoc",
            str(PANDOC_MD),
            "-f",
            "gfm+tex_math_dollars",
            "-t",
            "latex",
            "--wrap=none",
            "-o",
            str(BODY_TEX),
        ],
        check=True,
    )

    tex = BODY_TEX.read_text(encoding="utf-8")

    # Convert Pandoc's longtable output to ordinary IEEE column-contained tables.
    tex = re.sub(
        r"\\begin\{longtable\}\[\]\{@\{\}([^}]*)@\{\}\}",
        r"\\begin{tabular}{\1}",
        tex,
    )
    tex = tex.replace("\\endfirsthead", "")
    tex = tex.replace("\\endhead", "")
    tex = tex.replace("\\endlastfoot", "")
    tex = tex.replace("\\toprule\\noalign{}", "\\toprule")
    tex = tex.replace("\\midrule\\noalign{}", "\\midrule")
    tex = tex.replace("\\bottomrule\\noalign{}", "\\bottomrule")
    tex = tex.replace("\\end{longtable}", "\\end{tabular}")
    tex = tex.replace(
        "\\begin{tabular}",
        "\\begin{adjustbox}{max width=\\columnwidth}\\begin{tabular}",
    )
    tex = tex.replace(
        "\\end{tabular}",
        "\\end{tabular}\\end{adjustbox}",
    )

    BODY_TEX.write_text(tex, encoding="utf-8")

if __name__ == "__main__":
    main()
