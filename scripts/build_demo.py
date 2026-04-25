from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from ground_effect_vlm import Wing, solve_wing  # noqa: E402

heights = [0.25, 0.3, 0.4, 0.5, 0.65, 0.8, 1, 1.25, 1.5, 2, 3, 5, 10, 50]
wing = Wing(aspect_ratio=4, span_panels=64, quarter_chord_height=50)
free = solve_wing(wing, 4, include_ground=False)
cases = []
for height in heights:
    solution = solve_wing(
        Wing(aspect_ratio=4, span_panels=64, quarter_chord_height=height),
        4,
        include_ground=True,
    )
    cases.append({
        "height": height,
        "clAtFourDegrees": solution.lift_coefficient,
        "cdiAtFourDegrees": solution.induced_drag_coefficient,
        "efficiency": solution.span_efficiency,
        "amplification": solution.lift_coefficient / free.lift_coefficient,
        "span": (solution.span_centres / solution.wing.span).round(7).tolist(),
        "circulation": (solution.circulation / np.max(solution.circulation)).round(7).tolist(),
    })
output = {
    "basisAlphaDegrees": 4,
    "freeAir": {"cl": free.lift_coefficient, "cdi": free.induced_drag_coefficient},
    "cases": cases,
}
(PROJECT_ROOT / "demo" / "data.json").write_text(json.dumps(output, separators=(",", ":")))
print(f"Wrote {len(cases)} verified ride-height states")
