# Automotive External Aerodynamics with OpenFOAM

Steady RANS simulations of a validation body and several road and race cars, built
and run in OpenFOAM v2606. Every case includes its complete setup, so you can
reproduce it with a single `./Allrun`. The results include force coefficients,
convergence histories and mesh-quality logs.

![Summary of force coefficients](summary.png)

## Results

| Case | Cells | Cd | Cl | Notes |
|---|---:|---:|---:|---|
| [Ahmed body, 25° slant](ahmed-body/) | 8.4 M | **0.268** ± 0.001 | +0.283 ± 0.078 | Validation case. Experiment: Cd ≈ 0.285 (−6 %) |
| [Ferrari 499P (LMH)](ferrari-499p/) | 4.7 M | 0.419 ± 0.002 | **−0.381** ± 0.019 | Only car producing net downforce; 85 % of it at the rear |
| [Chevrolet Corvette](corvette/) | 3.7 M | 0.340 ± 0.002 | +0.118 ± 0.006 | Most steady solution of the set |
| [Ford Mustang](mustang/) | 3.9 M | 0.402 ± 0.008 | −0.158 ± 0.035 | Restarted from iteration 1300 after an interrupted run |
| [motorBike (OpenFOAM tutorial)](motorbike/) | 0.35 M | 0.416 ± 0.001 | +0.071 ± 0.002 | Baseline used to learn the workflow |

Coefficients are the mean ± one standard deviation over the last 300 iterations,
referenced to each vehicle's frontal area. The frontal areas were measured from the
geometry with [`tools/frontal_area.py`](tools/frontal_area.py).

## Method (common to all cases)

| | |
|---|---|
| Solver | `simpleFoam`: steady, incompressible, SIMPLE algorithm |
| Turbulence | k-ω SST, wall functions (mean y+ ≈ 60–90 where measured) |
| Freestream | 40 m/s (20 m/s for motorBike), ν = 1.5×10⁻⁵ m²/s |
| Ground | Moving wall at freestream speed (no ground boundary layer) |
| Wheels | Stationary (not rotating) |
| Mesh | `blockMesh` background + `snappyHexMesh` (castellated, snapped, 1 prism layer) |
| Discretisation | Bounded `linearUpwindV` for momentum, GAMG for pressure |
| Initialisation | `potentialFoam` |
| Run | 1500 iterations (500 for motorBike), decomposed across 6 cores |

## Lessons learned

- **Check that the reference values match the geometry.** The 499P was first run with the
  Mustang's reference area, carried over from the Mustang case. That made its Cd and Cl 28 % too small.
  Coefficients scale exactly with 1/Aref, so I corrected them in post-processing. The
  pitching moments can't be corrected this way, because the moment reference point also
  differed. The corrected setup is the one in the repo.
- **Measure reference areas; don't estimate them.** `frontal_area.py` projects the STL onto
  the y–z plane. For the Corvette it gave 1.989 m² against a 1.95 m² estimate, a 2 % change in Cd.
- **Steady RANS on bluff bodies doesn't settle completely.** Lift on the Ahmed body
  and Mustang oscillates by ±25 % while drag stays within ±2 %. Averaging over a window is
  necessary, and an unsteady (URANS/DES) run would be the next step.
- **Downloaded visual models need repair before meshing.** The Sketchfab cars had to be
  cleaned, welded and closed into watertight surfaces before `snappyHexMesh` would
  produce a usable mesh.

## Repository layout

```
<case>/
  README.md        setup, mesh, results, discussion
  case/            system/, constant/, 0.orig/, Allrun, Allclean  → run with ./Allrun
  results/
    forceCoeffs1/  coefficient history (coefficient.dat)
    solverInfo1/   residual history
    yPlus/         y+ statistics (where computed)
    logs/          blockMesh, snappyHexMesh, checkMesh logs; solver log (.gz)
    convergence.png
tools/
  frontal_area.py  frontal area from an STL
  plot_results.py  regenerates every plot and the summary table numbers
```

## Reproducing

```bash
source /usr/lib/openfoam/openfoam2606/etc/bashrc   # or your OpenFOAM install
cd ahmed-body/case
./Allrun                    # mesh, decompose, solve on 6 cores, reconstruct
cd ../.. && python3 tools/plot_results.py
```

The geometry is stored gzipped (`*.stl.gz`); OpenFOAM reads it directly. The full
cases are 10–20 GB each once run, so meshes and field data are not tracked.

## Geometry credits

The car models come from Sketchfab under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). They were modified for CFD:
repaired, made watertight, rotated and scaled.

- Ferrari 499P: "TODO model title" by TODO author, TODO link
- Chevrolet Corvette: "TODO model title" by TODO author, TODO link
- Ford Mustang: "TODO model title" by TODO author, TODO link

The Ahmed body follows the geometry of Ahmed, Ramm & Faltin (1984), SAE 840300.
The motorBike geometry ships with the OpenFOAM tutorials.
