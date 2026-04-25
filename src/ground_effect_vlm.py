from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class Wing:
    aspect_ratio: float = 4.0
    chord: float = 1.0
    quarter_chord_height: float = 1.0
    span_panels: int = 48
    wake_lengths: float = 80.0

    def __post_init__(self) -> None:
        if self.aspect_ratio <= 0 or self.chord <= 0 or self.quarter_chord_height <= 0:
            raise ValueError("aspect ratio, chord, and quarter-chord height must be positive")
        if self.span_panels < 8:
            raise ValueError("at least eight span panels are required")
        if self.wake_lengths < 20:
            raise ValueError("wake must extend at least twenty chords")

    @property
    def span(self) -> float:
        return self.aspect_ratio * self.chord

    @property
    def area(self) -> float:
        return self.span * self.chord


@dataclass(frozen=True)
class VLMSolution:
    wing: Wing
    alpha_degrees: float
    include_ground: bool
    span_centres: FloatArray
    panel_widths: FloatArray
    circulation: FloatArray
    downwash: FloatArray
    lift_coefficient: float
    induced_drag_coefficient: float
    span_efficiency: float
    ground_boundary_max_normal_velocity: float


def finite_vortex_velocity(point: FloatArray, start: FloatArray, end: FloatArray) -> FloatArray:
    """Velocity induced by a unit-strength finite vortex segment."""
    first = point - start
    second = point - end
    segment = end - start
    cross = np.cross(first, second)
    cross_squared = float(cross @ cross)
    first_norm = float(np.linalg.norm(first))
    second_norm = float(np.linalg.norm(second))
    if cross_squared < 1e-24 or first_norm < 1e-12 or second_norm < 1e-12:
        return np.zeros(3)
    scale = segment @ (first / first_norm - second / second_norm)
    return cross * scale / (4 * np.pi * cross_squared)


def _reflect(point: FloatArray) -> FloatArray:
    reflected = point.copy()
    reflected[2] *= -1
    return reflected


def _segments(wing: Wing, left_y: float, right_y: float) -> tuple[tuple[FloatArray, FloatArray], ...]:
    x_bound = 0.25 * wing.chord
    x_far = x_bound + wing.wake_lengths * wing.chord
    left = np.array([x_bound, left_y, wing.quarter_chord_height])
    right = np.array([x_bound, right_y, wing.quarter_chord_height])
    far_left = np.array([x_far, left_y, wing.quarter_chord_height])
    far_right = np.array([x_far, right_y, wing.quarter_chord_height])
    return ((far_left, left), (left, right), (right, far_right))


def horseshoe_velocity(
    point: FloatArray,
    wing: Wing,
    left_y: float,
    right_y: float,
    include_ground: bool = True,
    trailing_only: bool = False,
) -> FloatArray:
    segments = _segments(wing, left_y, right_y)
    selected = (segments[0], segments[2]) if trailing_only else segments
    velocity = sum((finite_vortex_velocity(point, start, end) for start, end in selected), np.zeros(3))
    if include_ground:
        velocity -= sum(
            (finite_vortex_velocity(point, _reflect(start), _reflect(end)) for start, end in selected),
            np.zeros(3),
        )
    return velocity


def _span_edges(wing: Wing) -> FloatArray:
    return np.linspace(-0.5 * wing.span, 0.5 * wing.span, wing.span_panels + 1)


def _ground_residual(wing: Wing, edges: FloatArray, circulation: FloatArray) -> float:
    samples_x = np.array([-0.5, 0.75, 3.0]) * wing.chord
    samples_y = np.linspace(-0.45 * wing.span, 0.45 * wing.span, 9)
    maximum = 0.0
    for x in samples_x:
        for y in samples_y:
            point = np.array([x, y, 0.0])
            velocity = sum(
                (
                    circulation[index]
                    * horseshoe_velocity(point, wing, edges[index], edges[index + 1], include_ground=True)
                    for index in range(wing.span_panels)
                ),
                np.zeros(3),
            )
            maximum = max(maximum, abs(float(velocity[2])))
    return maximum


def solve_wing(wing: Wing, alpha_degrees: float, include_ground: bool = True) -> VLMSolution:
    """Solve one chordwise row of horseshoe vortices for a pitched rectangular wing."""
    alpha = np.deg2rad(alpha_degrees)
    chord_direction = np.array([np.cos(alpha), 0.0, -np.sin(alpha)])
    normal = np.array([np.sin(alpha), 0.0, np.cos(alpha)])
    freestream = np.array([1.0, 0.0, 0.0])
    edges = _span_edges(wing)
    centres = (edges[:-1] + edges[1:]) / 2
    widths = np.diff(edges)
    control_xz = np.array([0.25 * wing.chord, 0.0, wing.quarter_chord_height]) + 0.5 * wing.chord * chord_direction
    controls = np.column_stack((
        np.full(wing.span_panels, control_xz[0]),
        centres,
        np.full(wing.span_panels, control_xz[2]),
    ))
    influence = np.empty((wing.span_panels, wing.span_panels))
    for target in range(wing.span_panels):
        for source in range(wing.span_panels):
            velocity = horseshoe_velocity(
                controls[target], wing, edges[source], edges[source + 1], include_ground=include_ground
            )
            influence[target, source] = velocity @ normal
    right_hand_side = np.full(wing.span_panels, -(freestream @ normal))
    circulation = np.linalg.solve(influence, right_hand_side)

    downwash = np.empty(wing.span_panels)
    for target, y in enumerate(centres):
        point = np.array([0.25 * wing.chord, y, wing.quarter_chord_height])
        velocity = sum(
            (
                circulation[source]
                * horseshoe_velocity(
                    point,
                    wing,
                    edges[source],
                    edges[source + 1],
                    include_ground=include_ground,
                    trailing_only=True,
                )
                for source in range(wing.span_panels)
            ),
            np.zeros(3),
        )
        downwash[target] = velocity[2]

    lift_coefficient = float(2 * np.sum(circulation * widths) / wing.area)
    induced_drag_coefficient = float(-2 * np.sum(circulation * downwash * widths) / wing.area)
    span_efficiency = float(
        lift_coefficient**2 / (np.pi * wing.aspect_ratio * induced_drag_coefficient)
    ) if induced_drag_coefficient > 0 else float("nan")
    ground_residual = _ground_residual(wing, edges, circulation) if include_ground else float("nan")
    return VLMSolution(
        wing,
        alpha_degrees,
        include_ground,
        centres,
        widths,
        circulation,
        downwash,
        lift_coefficient,
        induced_drag_coefficient,
        span_efficiency,
        ground_residual,
    )


def lifting_line_slope(aspect_ratio: float, section_slope: float = 2 * np.pi, efficiency: float = 1) -> float:
    """Prandtl finite-wing lift slope per radian."""
    return float(section_slope / (1 + section_slope / (np.pi * efficiency * aspect_ratio)))
