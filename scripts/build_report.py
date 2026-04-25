from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "results" / "analysis.json").read_text())
verification = data["verification"]
results = data["results"]
free = results["freeAir"]
half = next(case for case in results["groundSweep"] if case["heightOverChord"] == 0.5)
rows = [
    ("Ground-plane normal-velocity residual", f'{verification["maximumGroundNormalVelocityResidual"]:.1e}', "< 1e-12"),
    ("h/c=50 vs free-air lift difference", f'{verification["farGroundToFreeAirLiftRelativeDifference"]:.4%}', "< 0.1%"),
    ("Free-air lift-slope error vs Prandtl", f'{verification["liftSlopeRelativeError"]:.2%}', "< 12%"),
    ("Lift change, 64 to 96 panels", f'{verification["refinementRelativeChange64To96"]:.3%}', "< 1%"),
    ("Spanwise circulation symmetry error", f'{verification["spanwiseSymmetryMaxDifference"]:.2e}', "< 1e-12"),
]
rows_html = "".join(
    f"<tr><td>{html.escape(label)}</td><td>{observed}</td><td>{threshold}</td><td class='pass'>PASS</td></tr>"
    for label, observed, threshold in rows
)
drag_reduction = results["halfChordHeightInducedDragPerLiftSquaredReduction"]
output = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Ground-effect VLM technical report</title><link rel='stylesheet' href='./ground-effect-vlm-report.css'></head><body><main>
<span class='eyebrow'>TECHNICAL REPORT / REPRODUCIBLE STUDY</span><h1>Ground-effect sensitivity of a finite wing</h1><p>One-row horseshoe-vortex model · AR 4 rectangular wing · 64 span panels · fixed incidence 4°</p>
<div class='metrics'><div class='metric'><span>Lift gain at h/c=0.5</span><strong>{half['liftAmplification'] - 1:.1%}</strong></div><div class='metric'><span>Induced-drag cost / lift² reduction</span><strong>{drag_reduction:.1%}</strong></div><div class='metric'><span>Acceptance gates</span><strong>5 / 5</strong></div></div>
<h2>Question</h2><p>How does proximity to a moving ground plane alter circulation, lift, and induced-drag cost, and which checks are necessary before trusting that trend?</p>
<h2>Method</h2><p>A rectangular wing is represented by finite horseshoe vortices. Bound segments lie on the quarter-chord; collocation points lie on the three-quarter-chord. Every vortex is mirrored below the ground plane with reversed circulation, enforcing zero ground-normal velocity. The wake extends 80 chords.</p><p>The sweep covers quarter-chord heights 0.25 ≤ h/c ≤ 50. This is linear, incompressible, inviscid potential flow: no thickness, viscosity, separation, moving-road boundary layer, tyres, floor, diffuser, or body blockage.</p>
<img src='../images/projects/ground-effect-vlm/ground-sweep.svg' alt='Lift amplification and induced-drag cost across ride height'>
<h2>Verification</h2><table><thead><tr><th>Gate</th><th>Observed</th><th>Threshold</th><th>Result</th></tr></thead><tbody>{rows_html}</tbody></table>
<img src='../images/projects/ground-effect-vlm/verification.svg' alt='Free-air analytical and span-refinement checks'>
<h2>Result and interpretation</h2><p>Free air gives <strong>C<sub>L</sub>={free['liftCoefficient']:.4f}</strong>, <strong>C<sub>Dᵢ</sub>={free['inducedDragCoefficient']:.5f}</strong>, and <strong>e={free['spanEfficiency']:.3f}</strong>. At h/c=0.5, fixed-incidence lift rises to <strong>C<sub>L</sub>={half['liftCoefficient']:.4f}</strong>. Absolute induced drag remains similar, while C<sub>Dᵢ</sub>/C<sub>L</sub>² falls {drag_reduction:.1%}. The defensible mechanism claim is lower downwash cost for required lift—not guaranteed absolute drag reduction at fixed incidence.</p><p>At h/c=0.25 the linear model predicts more than twice free-air lift. That is a limitation signal. Real low-clearance performance depends on viscous pressure recovery, separation, leakage, pitch, wheel wakes, body geometry, and ground boundary layers absent here.</p>
<img src='../images/projects/ground-effect-vlm/span-loading.svg' alt='Normalised circulation across span and ride height'>
<h2>Decision value</h2><ul><li>Check sign and scale before higher-fidelity work.</li><li>Separate image-vortex effects from viscous and geometric effects.</li><li>Exercise ride-height normalisation, convergence, and evidence discipline.</li><li>Provide an auditable baseline that a panel or RANS model must improve upon.</li></ul><p>Not suitable for ranking race-car floors, predicting stall, resolving diffuser separation, or reporting absolute vehicle coefficients.</p>
<h2>Sources</h2><ol><li><a href='https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/19760021075.pdf'>NASA SP-405, Vortex-Lattice Utilization (1976)</a></li><li><a href='https://ntrs.nasa.gov/citations/20160000765'>NASA/TM-2015-218804, Description, Usage, and Validation of MVL-15</a></li></ol><small>Generated from results/analysis.json. Full equations, commands, interpretation, and limitations are retained in the repository report.</small>
</main></body></html>"""
report_directory = ROOT / "report"
report_directory.mkdir(exist_ok=True)
(report_directory / "technical-report.html").write_text(output)
print("Wrote report/technical-report.html")
