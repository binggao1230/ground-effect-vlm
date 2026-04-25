# Ground-effect sensitivity of a finite wing

## Question

How does proximity to a moving ground plane alter the circulation, lift, and induced-drag cost of a finite wing, and which checks are necessary before trusting that trend?

## Method

A rectangular wing of aspect ratio 4 is represented by one chordwise row of finite horseshoe vortices. Bound segments lie on the quarter-chord; control points lie on the three-quarter-chord. The linear system enforces zero normal velocity at each control point. Semi-infinite trailing legs are approximated by wake segments 80 chords long.

The ground boundary uses the method of images. Every real vortex segment at $z>0$ is mirrored to $z<0$ with reversed circulation. The paired velocity field has zero normal component at $z=0$, which is checked directly at 257 ground-plane samples after solving.

All reported sensitivity cases use 64 uniform spanwise panels and $\alpha=4°$. The height is quarter-chord height divided by chord. The sweep is deliberately bounded at $h/c=0.25$: the formulation has no thickness, viscosity, separation, moving-road boundary layer, or vehicle-body interference, so still lower clearances would amplify a linearised singular mechanism rather than add useful fidelity.

## Verification gates

| Gate | Observed | Threshold | Result |
|---|---:|---:|---|
| Ground-plane normal-velocity residual | 0.0 | $<10^{-12}$ | PASS |
| $h/c=50$ vs free-air lift difference | 0.00335% | <0.1% | PASS |
| Free-air lift-slope error vs Prandtl finite-wing estimate | 11.01% | <12% | PASS |
| Lift change, 64 to 96 span panels at $h/c=1$ | 0.258% | <1% | PASS |
| Spanwise circulation symmetry error | $1.94\times10^{-16}$ | $<10^{-12}$ | PASS |

The analytical lift-slope gate is intentionally loose. A single chordwise row, finite wake, uniform panel spacing, and the classical lifting-line estimate are not identical models. Agreement at the expected scale plus refinement and far-ground recovery is the defensible claim; exact agreement would be suspicious.

## Results

At 4° in free air, the model gives $C_L=0.2615$, $C_{D_i}=0.00549$, and span efficiency $e=0.990$. At $h/c=0.5$, fixed-incidence lift rises to $C_L=0.3461$, a 32.37% amplification. Absolute induced drag remains similar at $C_{D_i}=0.00559$, but induced drag per lift squared falls 41.95% relative to free air. This is the useful mechanism result: the image system weakens downwash cost for a required lift, not a promise of free absolute drag reduction at fixed incidence.

At $h/c=0.25$, the linear model predicts $C_L=0.5419$, more than twice the free-air result. That endpoint is a warning as much as a result. A real low-clearance package would couple ground boundary layers, finite thickness, pressure recovery, separation, leakage, pitch, ride-height gradients, wheels, and body geometry. None exist here.

The normalised span loading becomes broader toward the tips as height falls. The derived span-efficiency factor exceeds one in ground effect because the conventional free-air $C_{D_i}=C_L^2/(\pi AR e)$ reference is being used in a different boundary-value problem; it is an efficiency indicator, not an Oswald factor for aircraft performance bookkeeping.

## Decision value

This tool is suitable for:

1. checking sign and scale before a higher-fidelity ground-effect study;
2. isolating image-vortex effects from viscous and geometric effects;
3. testing ride-height sweep discipline, normalisation, and numerical convergence;
4. generating an auditable baseline that a panel method or RANS model must improve upon.

It is not suitable for ranking race-car floor geometries, predicting stall, resolving diffuser separation, or reporting absolute vehicle coefficients.

## Sources

- NASA, *Vortex-Lattice Utilization*, NASA SP-405, 1976. https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/19760021075.pdf
- Ozoroski et al., *Description, Usage, and Validation of the MVL-15 Modified Vortex Lattice Analysis Capability*, NASA/TM-2015-218804. https://ntrs.nasa.gov/citations/20160000765
- The public NASA MVL-15 description explicitly identifies the base vortex-lattice method as inviscid and linearised; its viscous extension exists because stall and other nonlinear effects are outside that base model.
