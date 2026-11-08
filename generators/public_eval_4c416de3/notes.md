# Corner-normalized motif completion

## Current rule and build

Public parent `4c416de3`; canonical rule ID `ee_4c416de3`. The authored general
Racket reference reproduces all three original demonstrations and the supplied
test answer. It uses no lookup table or fixture access.

Infer a nonblack modal background and black-frame corner axes. Each corner has
at least two visible black cells among its first three inward steps on each arm.
Assign nonbackground/nonblack marks to their nearest corner, normalize by inward
axes, and learn the maximal complete motif. Recolor and reflect that motif into
every marked corner; preserve unrelated input cells and clip at the canvas edge.
The independent Python claim oracle rejects inconsistent/ambiguous generated
motifs. Ties use deterministic row-major order; the admitted grammar avoids
conflicting ties. The finite parent examples do not uniquely specify arbitrary
out-of-grammar behavior.

Parameter `copy_extent`: `full` is byte-identical to `reference.rkt`; `outside`
copies only offsets with at least one nonpositive inward coordinate (frame or
exterior), retaining original interior marks. This changes which geometry is
completed without discarding exemplar inference or corner-relative orientation.
Canonical source is duplicated exactly inside the native resource directory.

The adapter independently supports 2–6 demos and 1–4 requested queries, retaining
all four private queries before taking a prefix. Inputs are matched across
settings. A separate presentation seed shuffles the full bank before any current
query is selected. Only train input/output and one query input are public.

## Grammar and diversity

Fresh 24–30-cell canvases, variable palette/background, motif handedness and
shape, one/two/four frames, repeated colors, incomplete marks at different
interior positions, clipped stamps and partially off-canvas frames. Four private
queries use source indices 100–103; index 103 is a 30×30 four-frame case touching
all canvas boundaries with sixteen active corners. These source indices never
appear in a public view and do not set presentation order.

The first demo contains an exterior-asymmetric motif; the second has four
frames and repeated source colors arranged so a global-color copy contaminates
other markers. Frame spacing prevents false corner crossings. This is a bounded
constructive grammar, not a claim to support arbitrary intersecting rectangles.

## Repairs and retained evidence

Two actual two-demo ambiguities were reproduced with twelve protected-Racket
evaluations and retained in `tests/retained_shortcuts.json`: seed 0/outside admits
transposition; seed 63/full admits a global-color motif. The former prefix had
symmetric exterior offsets, and the latter did not force visibly harmful
cross-frame color contamination. Both are now constructively taught.

A broader sweep found seed 15/index 4 placing two frames one cell apart, which
created false corner intersections and stole exemplar cells. A failing regression
now pins the repair: separate the frames by five cells. No rejection/seed reroll
is used to hide these cases.

Final local suite: 41 tests passed. Authoring preflight verifies all original
labels, canonical base generation, and both settings on seeds 17/43 at two demos
and four queries. The final audit covers 64 seeds, both settings and every demo
count 2–6 (640 nested lesson views; 5,120 reused pair exposures), with no
query-changing survivors among sixteen executable Python rivals. Separate
maximum-demo checks and a causal replay use protected Racket.

Causal dependency: infer normalized motif offsets and oriented corner records,
then consume those records when stamping. On the source-bound outside-setting
30×30 witness, replacing the motif with a single corner cell changes 29 output
cells. The complete runtime identity is retained separately from the required
witness marker. Sixteen hashed single-query exports pass metadata/future-query
invariance checks. No universal uniqueness or measured training benefit claimed.

## Reproduction and status

From packet root, use `review.py run` with payload paths rooted in WORK/repo:

```
python3 review.py run python3 -m pytest generators/public_eval_4c416de3/tests -q
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_4c416de3 --root . --out ../checks/public_eval_4c416de3/NEW-preflight
python3 review.py run python3 generators/public_eval_4c416de3/workspace/parametric/audit.py --preflight ../checks/public_eval_4c416de3/NEW-preflight/preflight.json --out ../checks/public_eval_4c416de3/NEW-audit --seeds 64
```

Current evidence: `checks/public_eval_4c416de3/preflight-final/` and
`checks/public_eval_4c416de3/audit-final/`. Earlier failed check logs are retained
as development evidence, not as final-source passes. Reviewer-ready; owner
registration, exact-source native qualification/acceptance, and training admission
are not performed.

## Current repeated-parent reconciliation

Preserve exact full/outside programs and broad corner parser. Port quarter-turn transport to incomplete marked corners while leaving completed source motifs unchanged. This consumes the same reflection-normalized motif recovered by the accepted parser, and matches the incoming rotate examples checked. Current source-bound evidence is in evidence/repeat-fourteenth-union, including per-return dispositions and any unresolved conflict. Qualification and acceptance in this private copy do not publish the candidate.
