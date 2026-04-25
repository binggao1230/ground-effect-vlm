from __future__ import annotations

import json
from pathlib import Path
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from ground_effect_vlm import Wing, lifting_line_slope, solve_wing  # noqa: E402

RESULTS_DIRECTORY = PROJECT_ROOT / "results"
RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
alpha = 4.0
aspect_ratio = 4.0
panel_count = 64
heights = np.array([0.25, 0.3, 0.4, 0.5, 0.65, 0.8, 1.0, 1.25, 1.5, 2.0, 3.0, 5.0, 10.0, 50.0])

started = time.perf_counter()
free_solution = solve_wing(
    Wing(aspect_ratio=aspect_ratio, span_panels=panel_count, quarter_chord_height=50),
    alpha,
    include_ground=False,
)
ground_solutions = [
    solve_wing(
        Wing(aspect_ratio=aspect_ratio, span_panels=panel_count, quarter_chord_height=float(height)),
        alpha,
        include_ground=True,
    )
    for height in heights
]
lift = np.array([solution.lift_coefficient for solution in ground_solutions])
drag = np.array([solution.induced_drag_coefficient for solution in ground_solutions])
efficiency = np.array([solution.span_efficiency for solution in ground_solutions])

alpha_samples = np.array([-4, -2, 0, 2, 4], dtype=float)
free_alpha_lift = np.array([
    solve_wing(
        Wing(aspect_ratio=aspect_ratio, span_panels=panel_count, quarter_chord_height=50),
        float(sample),
        include_ground=False,
    ).lift_coefficient
    for sample in alpha_samples
])
observed_slope = float(np.polyfit(np.deg2rad(alpha_samples), free_alpha_lift, 1)[0])
theory_slope = lifting_line_slope(aspect_ratio)
slope_relative_error = abs(observed_slope - theory_slope) / theory_slope

refinement_panels = [16, 24, 32, 48, 64, 96]
refinement = [
    solve_wing(Wing(aspect_ratio=aspect_ratio, span_panels=count, quarter_chord_height=1), alpha)
    for count in refinement_panels
]
refinement_lift = [solution.lift_coefficient for solution in refinement]
refinement_change = abs(refinement_lift[-2] - refinement_lift[-1]) / abs(refinement_lift[-1])
far_ground_change = abs(ground_solutions[-1].lift_coefficient - free_solution.lift_coefficient) / abs(free_solution.lift_coefficient)
wall_residual = max(solution.ground_boundary_max_normal_velocity for solution in ground_solutions)
monotonic_lift = bool(np.all(np.diff(lift) < 0))
half_chord_index = int(np.where(heights == 0.5)[0][0])
one_chord_index = int(np.where(heights == 1.0)[0][0])
analysis_seconds = time.perf_counter() - started

summary = {
    "project": "Ground Effect VLM",
    "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "configuration": {
        "planform": "rectangular finite wing",
        "aspectRatio": aspect_ratio,
        "alphaDegrees": alpha,
        "spanPanels": panel_count,
        "wakeLengthsInChords": 80,
        "heightDefinition": "quarter-chord height / chord",
        "heightSweep": heights.tolist(),
    },
    "verification": {
        "prandtlLiftSlopePerRadian": theory_slope,
        "vlmFreeAirLiftSlopePerRadian": observed_slope,
        "liftSlopeRelativeError": slope_relative_error,
        "farGroundToFreeAirLiftRelativeDifference": far_ground_change,
        "maximumGroundNormalVelocityResidual": wall_residual,
        "refinementPanels": refinement_panels,
        "refinementLiftCoefficients": refinement_lift,
        "refinementRelativeChange64To96": refinement_change,
        "spanwiseSymmetryMaxDifference": float(np.max(np.abs(free_solution.circulation - free_solution.circulation[::-1]))),
    },
    "results": {
        "freeAir": {
            "liftCoefficient": free_solution.lift_coefficient,
            "inducedDragCoefficient": free_solution.induced_drag_coefficient,
            "spanEfficiency": free_solution.span_efficiency,
        },
        "groundSweep": [
            {
                "heightOverChord": float(height),
                "liftCoefficient": solution.lift_coefficient,
                "inducedDragCoefficient": solution.induced_drag_coefficient,
                "spanEfficiency": solution.span_efficiency,
                "liftAmplification": solution.lift_coefficient / free_solution.lift_coefficient,
            }
            for height, solution in zip(heights, ground_solutions)
        ],
        "halfChordHeightLiftAmplification": lift[half_chord_index] / free_solution.lift_coefficient,
        "oneChordHeightLiftAmplification": lift[one_chord_index] / free_solution.lift_coefficient,
        "halfChordHeightInducedDragPerLiftSquaredReduction": 1 - (
            drag[half_chord_index] / lift[half_chord_index] ** 2
        ) / (free_solution.induced_drag_coefficient / free_solution.lift_coefficient**2),
    },
    "performance": {"analysisSeconds": analysis_seconds},
    "acceptance": {
        "groundBoundaryResidualBelowOneTrillionth": bool(wall_residual < 1e-12),
        "farGroundMatchesFreeAirWithinPointOnePercent": bool(far_ground_change < 0.001),
        "freeAirLiftSlopeWithinTwelvePercentOfPrandtl": bool(slope_relative_error < 0.12),
        "spanRefinementChangeBelowOnePercent": bool(refinement_change < 0.01),
        "liftAmplificationMonotonicOverDeclaredSweep": monotonic_lift,
    },
}
(RESULTS_DIRECTORY / "analysis.json").write_text(json.dumps(summary, indent=2) + "\n")

plt.style.use("dark_background")
accent = "#0f766e"
orange = "#c2410c"
figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))
figure.patch.set_facecolor("#ffffff")
for axis in axes:
    axis.set_facecolor("#ffffff")
    axis.grid(color="#e2e8f0", alpha=0.4)
axes[0].semilogx(heights, lift / free_solution.lift_coefficient, "o-", color=accent)
axes[0].axhline(1, color="#64748b", linestyle="--", label="free air")
axes[0].set(xlabel="Quarter-chord height $h/c$", ylabel="$C_L / C_{L,\\infty}$", title="Fixed-incidence lift amplification")
axes[0].invert_xaxis()
axes[0].legend(frameon=False)
normalised_drag = drag / lift**2
free_normalised_drag = free_solution.induced_drag_coefficient / free_solution.lift_coefficient**2
axes[1].semilogx(heights, normalised_drag / free_normalised_drag, "s-", color=orange)
axes[1].axhline(1, color="#64748b", linestyle="--")
axes[1].set(xlabel="Quarter-chord height $h/c$", ylabel="$(C_{D_i}/C_L^2)/(C_{D_i}/C_L^2)_∞$", title="Induced-drag cost per lift²")
axes[1].invert_xaxis()
figure.tight_layout()
figure.savefig(RESULTS_DIRECTORY / "ground-sweep.svg")
plt.close(figure)

figure, axis = plt.subplots(figsize=(9.5, 4.8))
figure.patch.set_facecolor("#ffffff")
axis.set_facecolor("#ffffff")
for height, color in [(50, "#64748b"), (1, accent), (0.5, orange), (0.25, "#fb7185")]:
    index = int(np.where(heights == height)[0][0])
    solution = ground_solutions[index]
    axis.plot(
        solution.span_centres / solution.wing.span,
        solution.circulation / np.max(solution.circulation),
        color=color,
        label="free-air limit" if height == 50 else f"h/c = {height:g}",
    )
axis.set(xlabel="$y/b$", ylabel="$Γ/Γ_{max}$", title="Ground proximity reshapes span loading")
axis.grid(color="#e2e8f0", alpha=0.4)
axis.legend(frameon=False)
figure.tight_layout()
figure.savefig(RESULTS_DIRECTORY / "span-loading.svg")
plt.close(figure)

figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))
figure.patch.set_facecolor("#ffffff")
for axis in axes:
    axis.set_facecolor("#ffffff")
    axis.grid(color="#e2e8f0", alpha=0.4)
axes[0].plot(alpha_samples, free_alpha_lift, "o-", color=accent, label="VLM free air")
axes[0].plot(alpha_samples, theory_slope * np.deg2rad(alpha_samples), "--", color="#64748b", label="Prandtl slope")
axes[0].set(xlabel="Angle of attack [deg]", ylabel="$C_L$", title="Analytical free-air check")
axes[0].legend(frameon=False)
axes[1].plot(refinement_panels, refinement_lift, "o-", color=orange)
axes[1].set(xlabel="Span panels", ylabel="$C_L$ at h/c=1", title="Spanwise refinement")
figure.tight_layout()
figure.savefig(RESULTS_DIRECTORY / "verification.svg")
plt.close(figure)

print(json.dumps({
    "freeAirLiftSlopeError": slope_relative_error,
    "farGroundChange": far_ground_change,
    "refinementChange": refinement_change,
    "halfChordLiftAmplification": summary["results"]["halfChordHeightLiftAmplification"],
    "halfChordDragPerLiftSquaredReduction": summary["results"]["halfChordHeightInducedDragPerLiftSquaredReduction"],
    "acceptance": summary["acceptance"],
}, indent=2))
if not all(summary["acceptance"].values()):
    raise SystemExit(1)
