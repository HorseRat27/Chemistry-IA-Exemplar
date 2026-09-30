import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from data import LABEL, SALTS

R = json.load(open("results.json"))
COLOR = {"NaCl": "#2a78d6", "KCl": "#eb6834", "CaCl2": "#1baf7a", "MgCl2": "#eda100"}
MARKER = {"NaCl": "o", "KCl": "s", "CaCl2": "^", "MgCl2": "D"}
LINE = {"NaCl": "-", "KCl": "-", "CaCl2": "--", "MgCl2": "--"}
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.8,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.dpi": 220,
})


def style(ax):
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def series(ax, s, xs, ys, es, label_xy=None, **kw):
    ax.errorbar(xs, ys, yerr=es, color=COLOR[s], marker=MARKER[s], ls=LINE[s], lw=1.8,
                ms=6.5, mec=SURFACE, mew=1.2, capsize=3, elinewidth=1.1, label=LABEL[s], **kw)
    if label_xy:
        ax.annotate(LABEL[s], label_xy, color=INK, fontsize=9.5, va="center")


# Figure 1: full concentration range.
fig, ax = plt.subplots(figsize=(7.2, 4.0))
style(ax)
ends = {"NaCl": 1900, "KCl": 2650, "CaCl2": 230, "MgCl2": 820}
for s in SALTS:
    p = R["summary"][s]
    series(ax, s, [q["c"] for q in p], [q["mean"] for q in p], [q["err"] for q in p],
           label_xy=(0.205, ends[s]))
ax.set_xlim(-0.008, 0.232)
ax.set_ylim(0, 13500)
ax.set_xlabel("Salt concentration, c / mol dm$^{-3}$")
ax.set_ylabel("Apparent swelling degree, S / %")
ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
ax.legend(frameon=False, ncol=4, loc="upper right", fontsize=9)
fig.tight_layout()
fig.savefig("../figures/fig1_swelling_vs_concentration.png")

# Figure 2: ln S vs ln c with least-squares lines and the Flory limiting slope.
fig, ax = plt.subplots(figsize=(7.2, 4.4))
style(ax)
for s in SALTS:
    p = [q for q in R["summary"][s] if q["target"] > 0]
    x = np.log([q["c"] for q in p])
    y = np.log([q["mean"] for q in p])
    e = [q["err"] / q["mean"] for q in p]
    f = R["fits"][s]
    xx = np.linspace(x.min() - 0.08, x.max() + 0.08, 20)
    ax.plot(xx, f["slope"] * xx + f["intercept"], color=COLOR[s], lw=1.2, ls=LINE[s], alpha=0.9)
    ax.errorbar(x, y, yerr=e, color=COLOR[s], marker=MARKER[s], ls="none", ms=6.5,
                mec=SURFACE, mew=1.2, capsize=3, elinewidth=1.1,
                label=f"{LABEL[s]}: gradient = {f['slope']:.2f} ± {f['u_slope']:.2f}".replace("-", "−"))
x0, y0 = np.log(0.05), 8.55
ax.plot([x0, np.log(0.2)], [y0, y0 - 0.6 * (np.log(0.2) - x0)], color=INK2, lw=1.2, ls=":")
ax.annotate("reference gradient −0.60 (Flory limit; vertical position arbitrary)", (np.log(0.058), 8.62), color=INK2, fontsize=8.5)
ax.set_xlabel("ln(c / mol dm$^{-3}$)")
ax.set_ylabel("ln(S / %)")
ax.set_ylim(5.8, 8.8)
ax.legend(frameon=False, fontsize=8.8, loc="lower left")
fig.tight_layout()
fig.savefig("../figures/fig2_loglog.png")

# Figure 3: swelling against ionic strength.
fig, ax = plt.subplots(figsize=(7.2, 4.0))
style(ax)
lab = {"NaCl": (0.207, 2110), "KCl": (0.207, 2420), "CaCl2": (0.61, 330), "MgCl2": (0.61, 610)}
for s in SALTS:
    p = [q for q in R["summary"][s] if q["target"] > 0]
    series(ax, s, [q["I"] for q in p], [q["mean"] for q in p], [q["err"] for q in p], label_xy=lab[s])
ax.axvline(0.15, color=INK2, lw=0.9, ls=":")
ax.annotate("equal I = 0.15 mol dm$^{-3}$", (0.158, 4450), color=INK2, fontsize=9)
ax.set_xlim(0, 0.70)
ax.set_ylim(0, 4700)
ax.set_xlabel("Ionic strength, I / mol dm$^{-3}$")
ax.set_ylabel("Apparent swelling degree, S / %")
ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
ax.legend(frameon=False, ncol=4, loc="upper right", fontsize=9, bbox_to_anchor=(1.0, 0.80))
fig.tight_layout()
fig.savefig("../figures/fig3_ionic_strength.png")
print("ok")
