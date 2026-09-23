#!/usr/bin/env python3
"""
Convergence and summary plots for every case in this repo.

For each case it reads results/forceCoeffs1/*/coefficient.dat and
results/solverInfo1/*/solverInfo.dat (stitching restarted runs together),
writes results/convergence.png, and writes summary.png at the repo root.
It also prints the mean and standard deviation of Cd and Cl over the
last AVG_WINDOW iterations, which are the numbers quoted in the READMEs.

Usage:  python3 tools/plot_results.py      (run from the repo root)
Needs:  numpy, matplotlib
"""
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AVG_WINDOW = 300

# Case folder -> (label, Aref used by the solver, correct Aref).
# Cd and Cl scale with 1/Aref, so a wrong Aref is fixed by multiplying by
# used/correct. See each case README for where the correct value came from.
CASES = {
    "ahmed-body":   ("Ahmed body 25°", 0.112,  0.112),
    "ferrari-499p": ("Ferrari 499P",   2.2695, 1.6437),  # ran with the Mustang's Aref
    "corvette":     ("Corvette",       1.95,   1.9891),  # estimate -> frontal_area.py
    "mustang":      ("Mustang",        2.2695, 2.2695),
    "motorbike":    ("motorBike",      0.75,   0.75),
}


def load_stitched(pattern, usecols=None, dtype=float):
    """Load every restart segment and keep, for each iteration, the latest run's value."""
    rows = {}
    for f in sorted(glob.glob(pattern), key=lambda p: float(p.split(os.sep)[-2])):
        data = np.genfromtxt(f, comments="#", usecols=usecols, dtype=dtype, invalid_raise=False)
        for r in np.atleast_2d(data):
            if not np.isnan(r[0]):
                rows[int(r[0])] = r
    return np.array([rows[k] for k in sorted(rows)])


def main():
    summary = []
    for case, (label, aref_used, aref_true) in CASES.items():
        k = aref_used / aref_true
        coeffs = load_stitched(f"{case}/results/forceCoeffs1/*/coefficient.dat")
        it, cd, cl = coeffs[:, 0], coeffs[:, 1] * k, coeffs[:, 4] * k
        # Ux, Uy, Uz, p initial residuals
        res = load_stitched(f"{case}/results/solverInfo1/*/solverInfo.dat", usecols=(0, 2, 5, 8, 13))

        w = slice(-AVG_WINDOW, None)
        s = dict(case=label, cd=cd[w].mean(), cd_sd=cd[w].std(), cl=cl[w].mean(), cl_sd=cl[w].std())
        summary.append(s)
        print(f"{label:16s} Cd = {s['cd']:.3f} ± {s['cd_sd']:.3f}   Cl = {s['cl']:+.3f} ± {s['cl_sd']:.3f}")

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
        ax1.plot(it, cd, label="Cd")
        ax1.plot(it, cl, label="Cl")
        ax1.axvspan(it[w][0], it[-1], color="0.9", zorder=0, label=f"averaging window ({AVG_WINDOW} it.)")
        lo, hi = np.percentile(np.r_[cd[len(cd) // 5:], cl[len(cl) // 5:]], [1, 99])
        pad = 0.15 * (hi - lo)
        ax1.set_ylim(lo - pad, hi + pad)
        ax1.set_ylabel("coefficient")
        ax1.set_title(f"{label}: force coefficients and residuals")
        ax1.legend(loc="upper right")
        ax1.grid(alpha=0.3)
        for i, name in enumerate(["Ux", "Uy", "Uz", "p"], start=1):
            ax2.semilogy(res[:, 0], res[:, i], label=name, lw=0.8)
        ax2.set_xlabel("iteration")
        ax2.set_ylabel("initial residual")
        ax2.legend(loc="upper right", ncol=4)
        ax2.grid(alpha=0.3, which="both")
        fig.tight_layout()
        fig.savefig(f"{case}/results/convergence.png", dpi=130)
        plt.close(fig)

    labels = [s["case"] for s in summary]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(x - 0.2, [s["cd"] for s in summary], 0.4, yerr=[s["cd_sd"] for s in summary], capsize=3, label="Cd")
    ax.bar(x + 0.2, [s["cl"] for s in summary], 0.4, yerr=[s["cl_sd"] for s in summary], capsize=3, label="Cl")
    ax.scatter([0 - 0.2], [0.285], marker="*", s=150, color="k", zorder=5, label="Ahmed body experiment (Cd)")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x, labels)
    ax.set_ylabel("coefficient")
    ax.set_title(f"Mean force coefficients (last {AVG_WINDOW} iterations, error bar = 1 std. dev.)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig("summary.png", dpi=130)


if __name__ == "__main__":
    main()
