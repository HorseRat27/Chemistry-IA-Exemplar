import json
import math
import statistics as st

import numpy as np

from data import BALANCE_U, CATION_CHARGE, FLASK_U_CM3, MOLAR_MASS, RAW, SALTS, VOLUME_DM3

TARGETS = [0.00, 0.05, 0.10, 0.15, 0.20]


def trial(salt, row):
    c_t, n, m, B, T, F = row
    H = T - B
    D = F - T
    S = D / H * 100
    rel_S = 2 * BALANCE_U / H + 2 * BALANCE_U / D
    c = m / MOLAR_MASS[salt] / VOLUME_DM3
    rel_c = (BALANCE_U / m + FLASK_U_CM3 / 50.0) if m else 0.0
    return dict(target=c_t, trial=n, m=m, B=B, T=T, F=F, H=H, D=D, S=S,
                uS=S * rel_S, relS=rel_S * 100, c=c, uc=c * rel_c)


def ionic_strength(salt, c):
    z = CATION_CHARGE[salt]
    return 0.5 * (c * z**2 + z * c * 1)


def total_ions(salt, c):
    return c * (1 + CATION_CHARGE[salt])


def main():
    out = {"trials": {}, "summary": {}, "fits": {}}
    for s in SALTS:
        rows = [trial(s, r) for r in RAW[s]]
        out["trials"][s] = rows
        summ = []
        for ct in TARGETS:
            g = [r for r in rows if r["target"] == ct]
            Ss = [r["S"] for r in g]
            mean = st.mean(Ss)
            sd = st.stdev(Ss)
            u_app = st.mean(r["uS"] for r in g)
            c = st.mean(r["c"] for r in g)
            uc = st.mean(r["uc"] for r in g)
            summ.append(dict(target=ct, S=Ss, mean=mean, sd=sd, rsd=sd / mean * 100,
                             u_app=u_app, rel_app=u_app / mean * 100,
                             err=max(sd, u_app), c=c, uc=uc,
                             I=ionic_strength(s, c), ions=total_ions(s, c),
                             half_range=(max(Ss) - min(Ss)) / 2))
        out["summary"][s] = summ

        pts = [p for p in summ if p["target"] > 0]
        x = np.log([p["c"] for p in pts])
        y = np.log([p["mean"] for p in pts])
        ey = np.array([p["err"] / p["mean"] for p in pts])
        slope, icpt = np.polyfit(x, y, 1)
        yhat = slope * x + icpt
        r2 = 1 - np.sum((y - yhat) ** 2) / np.sum((y - y.mean()) ** 2)
        n = len(x)
        se = math.sqrt(np.sum((y - yhat) ** 2) / (n - 2) / np.sum((x - x.mean()) ** 2))
        # Steepest / shallowest lines through the error bars of the first and last points.
        steep = ((y[-1] - ey[-1]) - (y[0] + ey[0])) / (x[-1] - x[0])
        shallow = ((y[-1] + ey[-1]) - (y[0] - ey[0])) / (x[-1] - x[0])
        out["fits"][s] = dict(slope=slope, intercept=icpt, r2=r2, se=se,
                              steep=steep, shallow=shallow,
                              u_slope=(shallow - steep) / 2,
                              k=math.exp(icpt))

    json.dump(out, open("results.json", "w"), indent=1)

    for s in SALTS:
        print(f"== {s}")
        for p in out["summary"][s]:
            print(f"  {p['target']:.2f} c={p['c']:.5f}±{p['uc']:.5f} I={p['I']:.4f} "
                  f"mean={p['mean']:.1f} sd={p['sd']:.1f} rsd={p['rsd']:.2f}% "
                  f"u_app={p['u_app']:.1f} ({p['rel_app']:.2f}%) err={p['err']:.1f} "
                  f"hr={p['half_range']:.1f}  S={[round(v,1) for v in p['S']]}")
        f = out["fits"][s]
        print(f"  slope={f['slope']:.3f} se={f['se']:.3f} r2={f['r2']:.4f} "
              f"steep={f['steep']:.3f} shallow={f['shallow']:.3f} ±{f['u_slope']:.3f} k={f['k']:.1f}")
    allrel = [r["relS"] for s in SALTS for r in out["trials"][s]]
    print("trial rel app unc range", min(allrel), max(allrel))
    allH = [r["H"] for s in SALTS for r in out["trials"][s]]
    print("H range", min(allH), max(allH), "mean", st.mean(allH))
    water = [v for s in SALTS for v in out["summary"][s][0]["S"]]
    print("all 12 water controls mean", st.mean(water), "sd", st.stdev(water))


if __name__ == "__main__":
    main()
