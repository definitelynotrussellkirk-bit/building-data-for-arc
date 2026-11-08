# Sparse-evidence candidate choice

This native authoring family keeps the source task's glyph-compatibility
reasoning and varies only the episode-fixed choice among the compatible glyphs.

| Private setting | Executed behavior |
| --- | --- |
| `candidate_choice=first` | Exact canonical Racket bytes: choose the earliest compatible glyph in reading order. |
| `candidate_choice=last` | Compute the same ordered compatible set, choose its last glyph, and expand it into the frame. |

The input sampler is independent of the hidden setting. It supports 2–6
independent demonstrations and 1–4 queries; ordinary qualification uses three
and four. Every scene has exactly two compatible glyphs plus incompatible
same-sized decoys. Candidate positions, areas, colors, mask dimensions, scales,
clue locations, and canvas sizes vary. The first two demonstrations reverse
candidate area and color ordering and place candidates at different indices,
while even/odd frame and fill colors defeat parity shortcuts. The fourth query
is a substantive 30×30 scene with a 23×23 frame and five top glyphs.

The required sequential dependency is literal. **A** maps sparse evidence through
the frame's block scale and produces the ordered compatible-glyph list. **B**
uses that input-dependent list to select its first or last element before
expansion. The retained `skip_candidate_filter_last` counterfactual selects the
last top glyph without A; query 4 has an incompatible final decoy, so protected
Racket produces a different output.

`teaching_report` checks 19 named Python rivals using demonstrations only and
reports any survivor that disagrees on a query. The bounded audit additionally
runs the two declared programs through protected Racket, tests matched inputs,
all supported demonstration counts, public first-turn invariance, and the exact
30×30 stress case. This is finite evidence, not universal uniqueness or a
measured-learning claim.

From the outer packet directory:

```bash
python3 review.py run python3 \
  generators/8d37d130fec1/workspace/parametric/audit.py \
  --out generators/8d37d130fec1/workspace/parametric/evidence/current

python3 review.py run python3 -m arcpuzzles parametric qualify 8d37d130fec1 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/8d37d130fec1/qualification --summary
```

Only the owner can accept the exact integrated bytes. Reviewer qualification is
not acceptance, and no training admission is implied.
