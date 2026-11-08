# Current decisions: 1e7c25b06dac

## Canonical repair

The authoritative program is unchanged (`rule_hash: eeff4ad960a5`, exact program
SHA-256 `e719f123c543810c5969ce8351273757afd202e99b9a26c10450bd37a00ca3f7`).
It fills only blank cells from their transposed partners; occupied reciprocal
cells retain their own values, so conflicting pairs need not become symmetric.

The previous version placed exactly three differently colored cells at fixed
lower-triangle coordinates. Lower-to-upper-only and fixed-coordinate rivals
therefore fit every ordinary draw. Its validator also rejected four of the five
canonical inputs because they contained four or five marks instead of three.
Version 2.1.0 varies positions and counts, guarantees sources in both triangles,
and admits canonical diagonal anchors and repeated colors. The reference rule
and frozen canonical data are untouched.

The sampler supports exact integer square sizes **3..30** through `grid_size`,
`grid_h`, and `grid_w`; supplied aliases must agree. Default sizes are 6..30,
with easy 6..10, medium 11..19, and hard 20..30. Explicit sizes override those
sampling bands. `palette_size` is 1..9 available nonzero colors (default 3), not
a guarantee that every color is used. Ordinary inputs have 2..min(size,12)
singleton off-diagonal source pairs plus 0..2 diagonal anchors. Positions span
the requested canvas; larger cases do not merely pad a fixed small pattern.

Only the documented controls are accepted. Previously advertised but unused
controls were removed; invalid controls, numeric coercions, conflicting sizes,
and false-valued texture names now fail explicitly. `texture` is `scattered`,
`no_marks`, `full_diagonal`, or `full_grid`; the final three are diagnostic
identity cases and intentionally fail `self_check`.

`self_check` validates exact integer ARC colors and at least one missing mirror.
Its reference-valid domain is broader than the sampler: an informative 2x2 grid
or an occupied reciprocal pair plus another active source can validate. Such
inputs are **validator/reference-only** support, not ordinary sampled support.

## Verification and useful commands

From the outer packet directory, using one configured Python interpreter:

```bash
python3 review.py run python3 generators/1e7c25b06dac/workspace/verify_transpose.py \
  --seed 1729 --demos 3 --queries 4 --sizes 3 6 20 30 \
  --out ../checks/transpose-replay-new.json

python3 review.py run python3 -m arcpuzzles generate 1e7c25b06dac \
  --count 1 --seed 1729 --override grid_size=30 --test 4 \
  --allow-unapproved --out ../checks/large-four-query-new.jsonl
```

The review's `checks/production-racket-final.json` binds final source bytes and
34 Racket executions: all five canonical pairs; four lessons with three demos
and four distinct queries each at sizes 3/6/20/30; and one occupied-partner
boundary. Every demonstration rejects the six declared rivals: identity,
transpose without retaining sources, lower-only copying, upper-only copying,
anti-diagonal copying, and legacy fixed-coordinate copying. This is bounded
finite-rival evidence, not proof of unique semantics or an automatic production
lesson gate. The existing production lesson hook remains undeclared.

`checks/production-four-query-final.jsonl` records the normal public generation
path: three demos, four distinct 30x30 queries, matching canonical reference,
zero recorded rejections, explicit research/unapproved provenance. The independent
`checks/adversarial-production/results.json` covers 336 sampler boundary draws,
deterministic replay, 72 difficulty/size checks, and malformed inputs/controls.
Focused regressions live in `tests/test_generator_1e7c25b06dac.py`.

## Public-evaluation inspiration: separate proposed extension

The assigned public task is `65b59efc`, compact sorted challenge-object SHA-256
`ee576437bcd000a274eb9a3ab26c827d293736f23a2940e227f575b1423ee067`.
Its color-keyed templates, shuffled placement masks, and aligned recoloring
swatches cannot be represented by E38's cell transpose-fill rule. Keep
`workspace/parametric/inspired_template_expansion.py` separate and proposed.

That prototype preserves the parent roles and dependencies while varying one
fixed episode parameter: identity versus transposed **coarse tile placement**;
template orientation stays unchanged. Its identity program reproduces the three
supplied parent demonstration outputs through Racket. The two public query
inputs can be executed but have no supplied gold labels; their answers remain
unverified predictions. Generated episodes share inputs across parameter settings,
expose independent demo/query counts, and include four distinct queries per setting.

See the prototype README and `checks/parametric/final-current/private/report.json` for
exact programs, parameters, hashes, demonstration-only finite-rival certificates,
strict public/private exports, tested boundaries, and remaining grammar limits.
Public challenge IDs hash the exact visible bytes; settings, seeds, programs,
and query labels stay private. Neither this review, its inspiration relationship,
nor successful packaging grants lineage verification, parametric acceptance,
production export eligibility, or training admission.

Next useful action: assess the canonical repair and separately decide whether the
inspired prototype merits a promotion adapter and source-qualified acceptance.
