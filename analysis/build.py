"""Fill the IA template with generated tables, count words, and export to .docx."""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from data import LABEL, RAW, SALTS

ROOT = Path(__file__).resolve().parent.parent
R = json.load(open(ROOT / "analysis" / "results.json"))


def sig_round(u, sf=2):
    if u == 0:
        return 0, 0
    dp = sf - 1 - int(math.floor(math.log10(abs(u))))
    return round(u, dp), max(dp, 0)


def pm(value, u, sf=2):
    if u == 0:
        return f"{value:,.0f}"
    place = sf - 1 - int(math.floor(math.log10(abs(u))))
    from decimal import ROUND_HALF_UP, Decimal
    q = Decimal(1).scaleb(-place)
    ur = float(Decimal(str(u)).quantize(q, rounding=ROUND_HALF_UP))
    vr = float(Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP))
    fmt = f"{{:,.{max(place, 0)}f}}"
    return f"{fmt.format(vr)} ± {fmt.format(ur)}"


def table(header, rows, caption):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join([":-:"] * len(header)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    out.append("")
    out.append(f"Table: {caption}")
    return "\n".join(out) + "\n"


def t_ions():
    rows = [("Na⁺", "+1", 102, "0.0098", "−424"), ("K⁺", "+1", 138, "0.0072", "−340"),
            ("Mg²⁺", "+2", 72, "0.0278", "−1963"), ("Ca²⁺", "+2", 100, "0.0200", "−1616")]
    return table(["Ion", "Charge", "Ionic radius / pm", "Charge ÷ radius / pm⁻¹",
                  "Enthalpy of hydration / kJ mol⁻¹"], rows,
                 "Table 1. Properties of the four cations (IBO, 2023).")


def t_variables():
    rows = [
        ("Independent", "Salt concentration: 0.00, 0.05, 0.10, 0.15, 0.20 mol dm⁻³",
         "Salt weighed (±0.001 g) and made up to 50.00 cm³ in a volumetric flask; actual concentration calculated from actual mass",
         "Five levels allow a trend and a power-law fit; the range includes the ionic strength of body fluids (≈0.15 mol dm⁻³)"),
        ("Independent", "Cation: Na⁺, K⁺, Mg²⁺, Ca²⁺",
         "Chloride salt of each cation used",
         "Compares charge (+1 against +2) and, within each charge, ion size and hydration"),
        ("Dependent", "Apparent swelling degree, S / %",
         "S = (F − T)/(T − B) × 100 from three balance readings",
         "Mass of solution absorbed per unit mass of dry polymer"),
        ("Controlled", "Anion (Cl⁻)", "All salts are chlorides",
         "Anions also affect swelling; a common anion isolates the cation effect"),
        ("Controlled", "Dry polymer mass (0.050 ± 0.002 g)", "Weighed into the bag; S uses each trial's actual mass",
         "Sample size changes how tightly the swollen gel fills the bag"),
        ("Controlled", "Solution volume (50.00 cm³)", "Whole contents of one volumetric flask",
         "Keeps cations in large excess so the external concentration stays constant"),
        ("Controlled", "Immersion time (120 s)", "Stopwatch started as the bag was submerged",
         "Swelling increases with time until equilibrium"),
        ("Controlled", "Draining and blotting", "Drained until dripping stopped; three 30 s blots on fresh tissue",
         "Surface liquid left on the bag would increase F"),
        ("Controlled", "Tea bag type and folding", "Identical bags, each folded twice",
         "The bag itself holds some solution; identical bags keep this similar"),
        ("Controlled", "Polymer", "Same sodium polyacrylate product throughout",
         "Cross-link density sets the maximum swelling"),
        ("Controlled (limited)", "Temperature", "All trials in the same laboratory; not measured",
         "Swelling depends on temperature (see Section 8)"),
    ]
    return table(["Type", "Variable", "How it was controlled or measured", "Why it matters"], rows,
                 "Table 2. Variables.")


def t_apparatus():
    rows = [("Electronic balance", "1", "±0.001 g"), ("Volumetric flask, 50.00 cm³ (Class A)", "1", "±0.06 cm³"),
            ("Beakers, 50 cm³ and 100 cm³", "1 each", "–"), ("Stopwatch", "1", "±0.01 s"),
            ("Weighing boats, spatula, glass rod, funnel, wash bottle, tweezers", "–", "–"),
            ("Empty paper tea bags", "60", "–"), ("Paper tissue", "–", "–"),
            ("Sodium polyacrylate granules", "≈3 g", "–"),
            ("NaCl, KCl, anhydrous CaCl₂, anhydrous MgCl₂", "≈3–6 g each", "–"),
            ("Distilled water", "≈3 dm³", "–")]
    return table(["Item", "Quantity", "Uncertainty"], rows, "Table 3. Apparatus and materials.")


def t_safety():
    rows = [
        ("Sodium polyacrylate powder", "Dust irritates eyes and airways; wet spills are very slippery",
         "Safety glasses; transferred gently with a spatula; spills swept up while dry"),
        ("Anhydrous CaCl₂", "Serious eye irritant; dissolves strongly exothermically",
         "Safety glasses; added to water gradually with stirring"),
        ("NaCl, KCl, MgCl₂", "Low hazard; mild eye irritants", "Safety glasses; hands washed after use"),
        ("Glassware", "Cuts from breakage", "Glassware checked for chips; breakages reported"),
        ("Swollen gel (environmental)", "Can block drains", "Disposed of in solid waste, never the sink"),
        ("Salt solutions (environmental)", "Dilute (≤ 0.20 mol dm⁻³) and of low toxicity",
         "Poured to drain with plenty of water; salt masses kept small"),
    ]
    return table(["Hazard", "Risk", "Precaution / disposal"], rows,
                 "Table 4. Safety and environmental considerations.")


def t_raw():
    parts = []
    for i, s in enumerate(SALTS):
        rows = [(f"{c:.2f}", n, f"{m:.3f}", f"{B:.3f}", f"{T:.3f}", f"{F:.3f}")
                for (c, n, m, B, T, F) in RAW[s]]
        parts.append(table(["Target c / mol dm⁻³", "Trial", "Salt mass, m / g ±0.001",
                            "Empty bag, B / g ±0.001", "Bag + dry polymer, T / g ±0.001",
                            "Final mass, F / g ±0.001"], rows,
                           f"Table {5 + i}. Raw data for {LABEL[s]}."))
    return "\n".join(parts)


def t_processed():
    rows = []
    for s in SALTS:
        for p in R["summary"][s]:
            c = "0 (water)" if p["target"] == 0 else pm(p["c"], p["uc"], 1)
            rows.append((LABEL[s], c, *[f"{v:,.0f}" for v in p["S"]], f"{p['mean']:,.0f}",
                         f"{p['sd']:,.0f}", f"{p['u_app']:,.0f}", pm(p["mean"], p["err"])))
    return table(["Salt", "Actual c / mol dm⁻³", "S₁ / %", "S₂ / %", "S₃ / %", "Mean / %",
                  "s / %", "Propagated ΔS / %", "Result / %"], rows,
                 "Table 9. Processed results. The result's uncertainty is the larger of s and "
                 "the propagated ΔS, rounded to 2 s.f.")


def t_fits():
    rows = []
    for s in SALTS:
        f = R["fits"][s]
        rows.append((LABEL[s], f"{f['slope']:.3f}", f"{f['steep']:.3f}", f"{f['shallow']:.3f}",
                     f"{f['slope']:.2f} ± {f['u_slope']:.2f}", f"{f['r2']:.3f}"))
    rows.append(("Flory limit", "−0.60", "", "", "−0.60", ""))
    return table(["Salt", "Least-squares gradient", "Steepest", "Shallowest", "n ± Δn", "R²"],
                 rows, "Table 10. Gradients of ln S against ln c.")


def word_count(md):
    body = md.split("# 9. References")[0]
    body = body.split("# 1. Introduction", 1)[1]
    body = re.sub(r"\$\$.*?\$\$", " ", body, flags=re.S)
    body = re.sub(r"\{\{[A-Z_]+\}\}", " ", body)
    lines = []
    for ln in body.splitlines():
        t = ln.strip()
        if t.startswith("#") or t.startswith("![") or t.startswith("Table:") or t.startswith(":::"):
            continue
        t = re.sub(r"^(\d+\.|-)\s+", "", t)
        lines.append(t)
    text = " ".join(lines)
    text = re.sub(r"\$[^$]*\$", " x ", text)
    text = re.sub(r"[*_~`]", "", text)
    return len([w for w in re.split(r"\s+", text) if w.strip()])


def style_docx(path):
    d = docx.Document(path)
    base = d.styles["Normal"]
    base.font.name = "Calibri"
    base.font.size = Pt(11)
    base.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    for name in ["Body Text", "First Paragraph", "Compact"]:
        if name in [s.name for s in d.styles]:
            st = d.styles[name]
            st.font.name = "Calibri"
            st.font.size = Pt(11)
            st.paragraph_format.space_after = Pt(6)
            st.paragraph_format.line_spacing = 1.15
    for name, size in [("Heading 1", 15), ("Heading 2", 12.5), ("Title", 22), ("Subtitle", 12)]:
        st = d.styles[name]
        st.font.name = "Calibri"
        st.font.size = Pt(size)
        st.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F) if name != "Subtitle" else RGBColor(0x52, 0x51, 0x4E)
        st.font.bold = name in ("Heading 1", "Heading 2", "Title")
        st.font.italic = False
        st.element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        st.element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    for name in ["Table Caption", "Image Caption", "Captioned Figure"]:
        if name in [s.name for s in d.styles]:
            st = d.styles[name]
            st.font.size = Pt(9.5)
            st.font.italic = True
            st.font.name = "Calibri"
    widths = {5: [0.8, 0.8, 1.2, 1.5, 1.8], 4: [1.0, 1.5, 1.9, 1.9], 3: [1.7, 2.2, 2.3],
              9: [0.55, 1.05, 0.55, 0.55, 0.55, 0.6, 0.45, 0.8, 1.15]}
    for t in d.tables:
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        ncols = len(t.columns)
        w = widths.get(ncols, [6.2 / ncols] * ncols)
        t.autofit = False
        grid = t._tbl.tblGrid
        for gc, wi in zip(grid.findall(qn("w:gridCol")), w):
            gc.set(qn("w:w"), str(int(wi * 1440)))
        for row in t.rows:
            for cell, wi in zip(row.cells, w):
                cell.width = Inches(wi)
            trPr = row._tr.get_or_add_trPr()
            cs = OxmlElement("w:cantSplit")
            trPr.append(cs)
        small = len(t.rows) <= 8
        for row in t.rows[:-1]:
            for cell in row.cells:
                for para in cell.paragraphs:
                    para.paragraph_format.keep_with_next = small
        tblPr = t._tbl.tblPr
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            el = OxmlElement(f"w:{edge}")
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "4")
            el.set(qn("w:color"), "9A9994")
            borders.append(el)
        tblPr.append(borders)
        ncols = len(t.columns)
        size = Pt(8) if ncols >= 8 else Pt(9)
        for i, row in enumerate(t.rows):
            for cell in row.cells:
                if i == 0:
                    shd = OxmlElement("w:shd")
                    shd.set(qn("w:val"), "clear")
                    shd.set(qn("w:color"), "auto")
                    shd.set(qn("w:fill"), "E8EEF5")
                    cell._tc.get_or_add_tcPr().append(shd)
                for para in cell.paragraphs:
                    para.paragraph_format.space_after = Pt(1)
                    para.paragraph_format.space_before = Pt(1)
                    for run in para.runs:
                        run.font.size = size
                        if i == 0:
                            run.font.bold = True
    for p in d.paragraphs:
        if p.style.name == "Table Caption":
            p.paragraph_format.keep_with_next = True
        if p.style.name == "Bibliography":
            p.paragraph_format.left_indent = Pt(24)
            p.paragraph_format.first_line_indent = Pt(-24)
            p.paragraph_format.space_after = Pt(6)
    d.save(path)


def main():
    src = (ROOT / "src" / "ia.md").read_text()
    wc = word_count(src)
    fills = {"TABLE_IONS": t_ions(), "TABLE_APPARATUS": t_apparatus(), "TABLE_VARIABLES": t_variables(), "TABLE_SAFETY": t_safety(),
             "TABLE_RAW": t_raw(), "TABLE_PROCESSED": t_processed(), "TABLE_FITS": t_fits(),
             "WORDCOUNT": f"{wc:,}"}
    for k, v in fills.items():
        src = src.replace("{{" + k + "}}", v)
    out_md = ROOT / "build" / "ia_filled.md"
    out_md.parent.mkdir(exist_ok=True)
    out_md.write_text(src)
    out = ROOT / "Chemistry_IA_HL_Exemplar.docx"
    import pypandoc
    pypandoc.convert_file(str(out_md), "docx", outputfile=str(out),
                          extra_args=["--resource-path", str(ROOT), "-f", "markdown+pipe_tables"])
    style_docx(out)
    print("word count:", wc)
    print("wrote", out)


if __name__ == "__main__":
    main()
