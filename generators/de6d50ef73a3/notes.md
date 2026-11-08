# Review notes: de6d50ef73a3

## Canonical repair

The exact authority is a **global nonzero tight crop** pasted at `(0,0)` on an
equal-size zero canvas. Canonical pairs include multicolor and disconnected
support, so `self_check` intentionally does not impose a single connected object.
The repaired generator validates exact controls, supports four observable shape
templates and 1–3 colors, accepts all five canonical inputs, and mirrors the
empty-input authority edge. The default Racket source remains byte-exact with
SHA-256 `6806b894d39bc71691bea3df3744c778148ca7c456dded5ad96ac8476c6f4ae5`.

Focused canonical contract evidence: initial RED 8 failed / 1 passed, separate
empty-authority RED 1 failed, final protected GREEN 10 passed.

## Proposed parametric family

`workspace/parametric/` adds `placement=top_left|marker_corner` without changing
the canonical domain. The teaching sampler uses one connected multicolor object
with a unique singleton marker at a tight-crop corner. The alternate setting
routes the full crop to the corresponding canvas corner. Inputs are matched
across settings, the minimum two demonstrations identify the selected rule among
six declared total rivals, and four queries cover all marker corners; the last is
a substantive 30×30 case.

Current evidence root:
`workspace/parametric/evidence/review-f37a3de5a3dfe30b/`

- complete changed-target tests: 34 passed;
- protected bounded probe: 20/20 episode requests, 160 independent-oracle
  matches, eight boundary labels, four native-worker compatibility jobs;
- authoring preflight: four jobs, 24 parametric labelled pairs, five canonical
  pairs, 32 protected Racket evaluations;
- causal witness: A derives the marker-corner route, B uses it to choose the
  destination; skipping A and forcing top-left changes the protected output;
- public projection: four episodes / 16 one-query views verified; first-turn
  privacy passed four first turns, 24 invariance checks, and four controls.

These are source-bound authoring and reviewer results only. `variant_approved`
and `training_admitted` remain false; owner qualification, acceptance, and
training admission were not performed.
