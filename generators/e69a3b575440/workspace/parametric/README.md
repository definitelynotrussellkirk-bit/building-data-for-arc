# Proposed quarter-turn parameter (isolated prototype)

This prototype keeps the canonical command-token/crop/dihedral family and varies
one rule parameter once per episode: `quarter_turn = clockwise | counterclockwise`. `clockwise` is the original/default setting and reproduces
the selected command-2 behavior. The other seven command mappings are unchanged.

Every complete episode has one demonstration for commands 1–8 and a command-2
query. The command-2 object is asymmetric, so the demonstration distinguishes
the two allowed settings before the query requires that distinction. The public
challenge JSON omits the hidden setting and query output. The hidden evidence
retains both exact Racket programs, hashes, Racket-derived outputs, seeds, and
rival checks.

Run from the outer extraction directory:

```bash
python3 review.py run python3 \
  generators/e69a3b575440/workspace/parametric/prototype.py \
  --out ../checks/parametric
```

Evidence is written to `WORK/checks/parametric/evidence.json`; public challenge
views are under `WORK/checks/parametric/public/`. This is a proposed prototype,
not a production API or approval of a new canonical rule.

Retained reviewer-run evidence is available at [evidence/manifest.json](evidence/manifest.json).
The manifest maps original `checks/parametric/` members to task-local files and
records their hashes and source identity. Results remain reviewer-reported;
retention does not approve the proposed variants or add a production API.
