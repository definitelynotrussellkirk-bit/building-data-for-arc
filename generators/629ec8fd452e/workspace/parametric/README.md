# Native true-hole / largest-hole color-relay family

`output_scope=all_holes` returns the exact accepted canonical Racket bytes and
keeps every same-color component containing a true enclosed background region.

`output_scope=largest_hole_color_relay` adds a non-collapsing sequential rule:

1. **A — topology and measurement:** identify true-hole components and sum all
   enclosed background-region cells for each component.
2. **Intermediate:** the color of the row-major first component with maximum
   total enclosed area.
3. **B — relay selection:** keep every disconnected component of that color,
   including solid or open components that A did not classify as hole sources.

The demonstrations are constructive. At the two-demo minimum they distinguish
both declared settings and the finite rival set in `verify.py`, including
rectangular-frame-only, largest-foreground, largest-single-cavity, source-only,
and first/last-source shortcuts. The four fixed query profiles include a lawful
30×30 boundary-stress case. Input generation is independent of the private
setting and query prefixes are stable.

From the packet root:

```sh
python3 review.py run python3 -m pytest -q \
  generators/629ec8fd452e/tests/test_parametric_largest_hole_relay.py \
  generators/629ec8fd452e/tests/test_parametric_audit_tools.py

python3 review.py run python3 \
  generators/629ec8fd452e/workspace/parametric/verify.py \
  --out generators/629ec8fd452e/workspace/parametric/evidence/current \
  --public-seeds 0,17 --demos 3 --audit-seeds 64

mkdir -p WORK/checks/629ec8fd452e

python3 WORK/check_public_exports.py \
  WORK/repo/generators/629ec8fd452e/workspace/parametric/evidence/current/public \
  --queries 1 --demos 3 \
  > WORK/checks/629ec8fd452e/public-check.raw.json

python3 review.py run python3 \
  generators/629ec8fd452e/workspace/parametric/verify.py \
  --normalize-public-check ../checks/629ec8fd452e/public-check.raw.json \
  --repo-root . \
  --out generators/629ec8fd452e/workspace/parametric/evidence/current/public-check.json

rm WORK/checks/629ec8fd452e/public-check.raw.json

python3 review.py run python3 -m arcpuzzles parametric qualify 629ec8fd452e \
  --out ../checks/629ec8fd452e/qualification --summary
```

`verify.py` is an authoring audit: it does not execute Racket. Native
qualification re-executes the exact Racket programs for every demonstration and
query label. The finite rival audit is not a proof of universal uniqueness.
Owner acceptance and downstream training admission remain separate decisions.
