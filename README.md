# Ground Effect VLM

A reproducible low-order study of a finite rectangular wing approaching a moving ground plane. The solver discretises the quarter-chord into finite horseshoe vortices, enforces flow tangency at three-quarter-chord collocation points, and mirrors every vortex below the ground plane with reversed circulation.

## Run

```bash
python3 -m unittest discover -s tests -v
python3 scripts/analyse.py
python3 scripts/build_demo.py
python3 scripts/publish_site.py
```

`results/analysis.json` is the machine-readable result. SVG figures, the interactive explorer data, and the technical report are regenerated from the same solver.

## Declared scope

- Rectangular, unswept, untwisted wing; aspect ratio 4.
- One chordwise row and 64 uniform spanwise panels.
- Linear, incompressible, inviscid, steady potential flow.
- Fixed geometric incidence of 4° and quarter-chord heights $0.25 \le h/c \le 50$.
- A moving ground plane: no boundary layer, road roughness, tyre interaction, diffuser, or body blockage.

This is a method and mechanism study, not a performance prediction for a race-car floor. The low-height amplification should not be extrapolated below the declared sweep or interpreted as viscous downforce.
