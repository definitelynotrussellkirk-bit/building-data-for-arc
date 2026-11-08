# dd6724624b9f — decode transform and recolor

**Kind:** per-puzzle generator
**Current version:** `3.0.1`
**Rule hash:** `8dd08a5ab5cb`
**Final reviewed source SHA-256:** `ba007156605bde9b4a2b797f8e7585b858f979ba2abedce28706c02bb383b188`

The input has a black background. The first two cells are controls: `(0,0)` selects one of six geometric transforms and `(0,1)` selects the output color. After clearing the controls, crop the sole 4-connected monochrome body, apply the selected transform, and recolor all occupied cells:

1. identity
2. flip left/right
3. flip up/down
4. rotate 90° clockwise
5. rotate 180°
6. rotate 90° counterclockwise

The generator exposes exact controls for height `8..16`, width `9..17`, transform code `1..6`, body size `3..8`, and eight color pairs. A lesson uses six ordered demonstrations, one per transform code. Production lessons are identifiable; arbitrary query rotations are diagnostic and may be ambiguous.

The prior imported version `2.1.0` used a stale five-code mapping and omitted code 6. Version `3.0.1` aligns generation with the unchanged selected authority and includes strict controls, observable override reporting, semantic rivals/witnesses, a rule mirror, and task-local regression tests.
