# Building the internship reports

From `report/long/`:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

From `report/short/`:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The short report defaults to `\totalpagecountfalse`. In this submission mode,
the cover, acknowledgements, and table of contents use roman numbering and the
ten-page body restarts at Arabic page 1. Set `\totalpagecounttrue` only for an
internal check that numbers the complete PDF continuously; it does not remove
or shorten the body.

Build artifacts (`.aux`, `.log`, `.toc`, and similar files) remain under the
ignored `report/` directory.

