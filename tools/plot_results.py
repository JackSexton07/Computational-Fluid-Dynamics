#!/usr/bin/env python3
"""
Convergence and summary plots for every case in this repo.

For each case it reads results/forceCoeffs1/*/coefficient.dat and
results/solverInfo1/*/solverInfo.dat (stitching restarted runs together),
writes results/convergence.png, and writes summary.png at the repo root.
It also prints the mean and standard deviation of Cd and Cl over the
last AVG_WINDOW iterations, which are the numbers quoted in the READMEs.
Cases with several runs (see PROGRESSIONS) also get results/progression.png,
comparing each run's Cd and Cl and overlaying their Cd histories.

Usage:  python3 tools/plot_results.py      (run from the repo root)
Needs:  numpy, matplotlib
"""
import glob
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AVG_WINDOW = 300

# A run killed mid-write leaves a truncated last line; genfromtxt skips it but warns.
warnings.filterwarnings("ignore", message="Some errors were detected")

# Case folder -> (label, Aref used by the solver, correct Aref).
# Cd and Cl scale with 1/Aref, so a wrong Aref is fixed by multiplying by
# used/correct. See each case README for where the correct value came from.
CASES = {
    "ahmed-body":   ("Ahmed body 25°", 0.112,  0.112),
    "ferrari-499p": ("Ferrari 499P",   2.2695, 1.6437),  # ran with the Mustang's Aref
    "ferrari-499p-v2": ("Ferrari 499P v2", 1.6762, 1.6762),
    "corvette":     ("Corvette C5",    1.95,   1.9891),  # estimate -> frontal_area.py
    "corvette-v2":  ("Corvette C5 v2", 1.989,  1.989),
    "mustang":      ("Mustang Shelby", 2.2695, 2.2695),
    "mustang-v2":   ("Mustang Shelby v2", 2.2695, 2.2695),
    "motorbike":    ("motorBike",      0.75,   0.75),
}

# Where each case keeps its force/residual histories (default: <case>/results).
# Multi-run cases point at the run quoted in their README.
RESULTS_DIR = {
    "corvette-v2": "corvette-v2/results/run3",
    "mustang-v2": "mustang-v2/results",
    "ferrari-499p-v2": "ferrari-499p-v2/results",
}

# Published or experimental Cd, drawn as a star on the summary chart.
REFERENCE_CD = {
    "ahmed-body":  (0.285, "Ahmed et al. 1984"),
    "corvette":    (0.29, "GM published"),
    "corvette-v2": (0.29, "GM published"),
}

# Step-by-step improvement studies: (label, results dir, Aref used / correct Aref).
PROGRESSIONS = {
    "corvette-v2": dict(
        title="Corvette C5: Cd and Cl through each change",
        reference=(0.29, "GM published Cd"),
        steps=[
            ("Original\n(small domain)", "corvette/results", 1.95 / 1.9891),
            ("Run 1\nlarge domain", "corvette-v2/results/run1", 1.0),
            ("Run 2\n+3 layers, near box", "corvette-v2/results/run2", 1.0),
            ("Run 3\n+rotating wheels", "corvette-v2/results/run3", 1.0),
        ],
    ),
    "ferrari-499p-v2": dict(
        title="Ferrari 499P: original vs. v2 (car on its tyres + Corvette v2 setup)",
        reference=None,
        steps=[
            ("Original\n(sunk 66 mm, small domain,\nstationary wheels)", "ferrari-499p/results", 2.2695 / 1.6437),
            ("v2\n(on its tyres, large domain,\n3 layers, rotating wheels)", "ferrari-499p-v2/results", 1.0),
        ],
    ),
    "mustang-v2": dict(
        title="Mustang Shelby: original setup vs. v2 (all three Corvette fixes at once)",
        reference=None,
        steps=[
            ("Original\n(small domain, 1 layer,\nstationary wheels)", "mustang/results", 1.0),
            ("v2\n(large domain, 3 layers,\nrotating wheels)", "mustang-v2/results", 1.0),
        ],
    ),
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


def plot_progression(case, spec):
    """Bar chart of mean Cd/Cl per run, plus the runs' Cd histories overlaid."""
    rows = []
    for label, rdir, k in spec["steps"]:
        c = load_stitched(f"{rdir}/forceCoeffs1/*/coefficient.dat")
        w = slice(-AVG_WINDOW, None)
        rows.append((label, c[:, 0], c[:, 1] * k, c[:, 1][w].mean() * k, c[:, 1][w].std() * k,
                     c[:, 4][w].mean() * k, c[:, 4][w].std() * k))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw=dict(width_ratios=[1.1, 1]))
    x = np.arange(len(rows))
    ax1.bar(x - 0.2, [r[3] for r in rows], 0.4, yerr=[r[4] for r in rows], capsize=3, label="Cd")
    ax1.bar(x + 0.2, [r[5] for r in rows], 0.4, yerr=[r[6] for r in rows], capsize=3, label="Cl")
    for xi, r in zip(x, rows):
        ax1.text(xi - 0.2, r[3] + 0.008, f"{r[3]:.3f}", ha="center", fontsize=9)
        ax1.text(xi + 0.2, r[5] + (0.008 if r[5] >= 0 else -0.025), f"{r[5]:.3f}", ha="center", fontsize=9)
    ref, ref_label = spec["reference"] or (None, None)
    if ref is not None:
        ax1.axhline(ref, color="k", ls="--", lw=1, label=f"{ref_label} ({ref})")
    ax1.set_xticks(x, [r[0] for r in rows], fontsize=9)
    ax1.set_ylabel("coefficient")
    lo = min(0, min(r[5] for r in rows) * 1.3)
    ax1.set_ylim(lo, max(r[3] for r in rows) * 1.2)
    ax1.axhline(0, color="k", lw=0.6)
    ax1.legend(loc="upper right")
    ax1.grid(axis="y", alpha=0.3)
    ax1.set_title(f"Mean of last {AVG_WINDOW} iterations (error bar = 1 std. dev.)", fontsize=10)
    for r in rows:
        ax2.plot(r[1], r[2], lw=0.9, label=r[0].replace("\n", " "))
    if ref is not None:
        ax2.axhline(ref, color="k", ls="--", lw=1)
    ax2.set_ylim(min([r[3] for r in rows] + ([ref] if ref else [])) - 0.03, max(r[3] for r in rows) + 0.04)
    ax2.set_xlabel("iteration")
    ax2.set_ylabel("Cd")
    ax2.legend(fontsize=8, loc="upper right")
    ax2.grid(alpha=0.3)
    ax2.set_title("Cd history of each run", fontsize=10)
    fig.suptitle(spec["title"])
    fig.tight_layout()
    fig.savefig(f"{case}/results/progression.png", dpi=130)
    plt.close(fig)
    for r in rows:
        print(f"    {r[0].replace(chr(10), ' '):28s} Cd = {r[3]:.4f}   Cl = {r[5]:+.4f}")


def main():
    summary = []
    for case, (label, aref_used, aref_true) in CASES.items():
        k = aref_used / aref_true
        rdir = RESULTS_DIR.get(case, f"{case}/results")
        coeffs = load_stitched(f"{rdir}/forceCoeffs1/*/coefficient.dat")
        it, cd, cl = coeffs[:, 0], coeffs[:, 1] * k, coeffs[:, 4] * k
        # Ux, Uy, Uz, p initial residuals
        res = load_stitched(f"{rdir}/solverInfo1/*/solverInfo.dat", usecols=(0, 2, 5, 8, 13))

        w = slice(-AVG_WINDOW, None)
        s = dict(key=case, case=label, cd=cd[w].mean(), cd_sd=cd[w].std(), cl=cl[w].mean(), cl_sd=cl[w].std())
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
        fig.suptitle(f"{label}: force coefficients and residuals")
        ax1.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False)
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

    for case, spec in PROGRESSIONS.items():
        print(f"{CASES[case][0]} progression:")
        plot_progression(case, spec)

    labels = [s["case"] for s in summary]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.bar(x - 0.2, [s["cd"] for s in summary], 0.4, yerr=[s["cd_sd"] for s in summary], capsize=3, label="Cd")
    ax.bar(x + 0.2, [s["cl"] for s in summary], 0.4, yerr=[s["cl_sd"] for s in summary], capsize=3, label="Cl")
    refs = [(i, REFERENCE_CD[s["key"]][0]) for i, s in enumerate(summary) if s["key"] in REFERENCE_CD]
    ax.scatter([i - 0.2 for i, _ in refs], [v for _, v in refs], marker="*", s=150, color="k", zorder=5,
               label="published / experimental Cd")
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
