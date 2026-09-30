# Chemistry IA Exemplar (HL)

A completed IB Chemistry HL internal assessment, kept as a reference for structure, data processing and evaluation.

**Topic:** the effect of the concentration (0.00–0.20 mol dm⁻³) of NaCl, KCl, MgCl₂ and CaCl₂ on the apparent swelling of sodium polyacrylate after 120 s.

## Files

| Path | What it is |
|---|---|
| `Chemistry_IA_HL_Exemplar.docx` / `.pdf` | The finished IA (2,962 words) |
| `src/ia.md` | The IA text (Markdown with LaTeX equations). Edit this, then rebuild |
| `analysis/data.py` | The 60 raw trials, transcribed from the lab spreadsheet |
| `analysis/process.py` | Means, standard deviations, propagated uncertainties, ionic strength and log–log fits → `results.json` |
| `analysis/figures.py` | Figures 1–3 → `figures/` |
| `analysis/build.py` | Generates the tables, counts words and exports the `.docx` |

## Rebuild

```bash
pip install python-docx pypandoc_binary matplotlib numpy
cd analysis && python3 process.py && python3 figures.py && python3 build.py
```

## Assumptions to confirm against the lab records

- CaCl₂ and MgCl₂ were **anhydrous** (M = 110.98 and 95.21 g mol⁻¹). If MgCl₂·6H₂O was used, every MgCl₂ concentration is 0.47 times the stated value.
- The volumetric flask is Class A (±0.06 cm³). This barely affects the results.
- Temperature was not measured. The IA says so and evaluates it.

The IB requires every IA to be the candidate's own work, so use this as a model rather than a template to copy.
