# Parametric transform-application family

Status: reviewer-ready proposal; owner exact-source acceptance remains required.
The production generator and canonical rule are unchanged.

Each episode fixes one private `application` setting while sharing identical
inputs across settings:

| setting | operation on panel C |
| --- | --- |
| `direct` | apply the unique transform inferred from A→B; exact canonical default |
| `inverse` | apply the inverse of that inferred transform |

Every demonstration uses a directional quarter-turn and therefore distinguishes
the two settings by its label alone. The adapter supports 2–6 demonstrations and
exactly four distinct queries revealed one at a time. Inputs range through
4×14, 5×17, 6×20, 7×23, 8×26, and 9×29 profiles with dense multicolor panels,
full boundary contact, and unique complete-panel transform orbits. The lawful
maximum is 9×29: the canonical grammar requires square panels and width
`3*rows+2`, so 10 rows already require width 32 and exact 30×30 is impossible.

Sequential dependency: step A compares transformed complete panel A against B
to infer the unique transform name. Step B cannot choose the direct or inverse
transform for C until that input-dependent name is known. `probe.py` retains a
protected-Racket witness where replacing inferred `cw` with `180` changes the
final output.

Run the focused tests from the packet root:

```bash
python3 review.py run python3 -m pytest \
  generators/105b239cb812/tests/test_parametric_transform_application.py \
  generators/105b239cb812/tests/test_parametric_probe.py -q
```

Refresh the native manifest, qualify, and then run `probe.py` against that exact
qualified `source_binding`. Public projections contain only demonstrations and
one masked query; settings, programs, query answers, future queries, and total
query count remain private.
