import sys
from pathlib import Path
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ground_effect_vlm import (  # noqa: E402
    Wing,
    finite_vortex_velocity,
    lifting_line_slope,
    solve_wing,
)


class GroundEffectVLMTests(unittest.TestCase):
    def test_finite_segment_reverses_with_orientation(self):
        point = np.array([0.5, 0.2, 0.4])
        start = np.array([0.0, 0.0, 0.0])
        end = np.array([1.0, 0.0, 0.0])
        np.testing.assert_allclose(
            finite_vortex_velocity(point, start, end),
            -finite_vortex_velocity(point, end, start),
            atol=1e-14,
        )

    def test_ground_image_enforces_zero_normal_velocity(self):
        result = solve_wing(Wing(span_panels=32, quarter_chord_height=0.5), 4, include_ground=True)
        self.assertLess(result.ground_boundary_max_normal_velocity, 1e-12)

    def test_zero_angle_and_spanwise_symmetry(self):
        result = solve_wing(Wing(span_panels=32), 0)
        self.assertAlmostEqual(result.lift_coefficient, 0, places=12)
        np.testing.assert_allclose(result.circulation, result.circulation[::-1], atol=1e-12)

    def test_far_ground_matches_free_air_and_lifting_line_scale(self):
        wing = Wing(aspect_ratio=4, span_panels=48, quarter_chord_height=50)
        ground = solve_wing(wing, 4, include_ground=True)
        free = solve_wing(wing, 4, include_ground=False)
        self.assertLess(abs(ground.lift_coefficient - free.lift_coefficient) / abs(free.lift_coefficient), 0.001)
        observed_slope = free.lift_coefficient / np.deg2rad(4)
        expected_slope = lifting_line_slope(wing.aspect_ratio)
        self.assertLess(abs(observed_slope - expected_slope) / expected_slope, 0.12)

    def test_span_refinement_and_ground_effect_trend(self):
        coarse = solve_wing(Wing(span_panels=48, quarter_chord_height=1), 4)
        fine = solve_wing(Wing(span_panels=64, quarter_chord_height=1), 4)
        self.assertLess(abs(fine.lift_coefficient - coarse.lift_coefficient) / abs(fine.lift_coefficient), 0.01)
        high = solve_wing(Wing(span_panels=48, quarter_chord_height=2), 4)
        low = solve_wing(Wing(span_panels=48, quarter_chord_height=0.5), 4)
        self.assertGreater(low.lift_coefficient, high.lift_coefficient)
        self.assertGreater(low.span_efficiency, high.span_efficiency)


if __name__ == "__main__":
    unittest.main()
