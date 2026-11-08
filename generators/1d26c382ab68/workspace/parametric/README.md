# Rotated-template native family

This opt-in adapter keeps the production generator and selected canonical rule
unchanged. `target=rotation_match` returns the exact selected canonical Racket
bytes. `target=turn_guided_reflection` is the separately proposed composition.

## Rule and grammar

Above a maroon divider is a blue chiral pentomino. Below are six same-colored,
same-sized objects from two different shape families. Each family contributes
one rotation candidate and two opposite reflected orientations. The upper
template determines which family is relevant; each scene has exactly one
rotational match to that template.

The default recolors that rotational match red. The alternative first finds
the match and its relative clockwise turn `t`, then recolors the candidate
equal to `rotate(reflect_lr(template), t)`. Reflection happens in the template's
frame before the inferred turn. This differs from reflecting the match directly
when the turn is odd.

With `M = R^t T`, the target also equals `R^(2t) F(M)`. Thus the downstream step
needs the matched shape and **turn parity**, not all four turn values. This is
input-derived contextual gating; it is not an iterative simulation. The causal
witness makes the operation-order error select a different real candidate.

The first two demonstrations share their complete lower scene. Changing the
upper template selects the other shape family, with opposite turn parity, so
both settings produce different lower outputs. This constructively defeats a
rule that ignores the template, fixed candidate positions, fixed reflection of
the match, and fixed reflected-template turns. `teaching_check` fits 22 named
hypotheses to demonstrations only and then inspects each query separately.
Finite rivals do not establish universal uniqueness.

`analyze()` is an observer for generated scenes, not a complete validator of
arbitrary hand-edited two-template scenes. It strictly checks the displayed
template's unique match and opposite reflected pair; the other family's
singleton/mirror multiplicity is guaranteed by construction, not fully checked
by that observer. Generated episodes and native qualification do not use an
external-grid intake path.

## Counts, sizes and determinism

`generate(seed, settings, demos, queries)` supports exact integer seeds in
`0..2^63-1`, 2–6 demonstrations and 1–4 queries independently. Use three demos
and four queries normally. The first turn is byte-identical for one versus four
queries at the same seed/settings/demo count. All pair inputs are distinct;
the uniqueness retry cap is 16 and exhaustion raises an error.

Input draws and teaching selection do not depend on the private setting.
The two settings share every input for the same request. Query profiles are
11×13 at scale 1, 20×22 and 24×26 at scale 2, and 30×30 at scale 3. At 30×30,
the template and six candidates contain 315 foreground cells, plus the 30-cell
divider. The larger canvas contains larger objects spread across both candidate
rows. The prototype restricts base shapes to chiral pentominoes; the unchanged
canonical production sampler still supports its original tetrominoes too.

## Public/private use

`program_solution`, settings, seeds, certificates and all query answers belong
to the controller. `model_view(episode, index)` returns only demonstration grids
and the selected query input. It has no planned count, future input or final-turn
marker. It is a projection helper, not a training loop or turn controller.
Serialize with `reviewer_support.public_challenge_bytes` and name the public
file with `public_challenge_id`. A four-query episode is controller data and
must not be passed wholesale to a model.

Python outputs are provisional claims. Native qualification re-executes both
setting programs on demonstrations and the selected program on queries through
protected Racket. Only that executed evidence supports labels in this return.

## Reproduce

From the outer packet, using the interpreter that passed `python-check`:

```bash
python3 review.py run python3 -m pytest -q generators/1d26c382ab68/tests/test_parametric_1d26c382ab68.py
python3 review.py run python3 generators/1d26c382ab68/workspace/parametric/audit.py --out ../checks/1d26c382ab68/new-audit
python3 review.py run python3 -m arcpuzzles parametric qualify 1d26c382ab68 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/1d26c382ab68/new-qualification --summary
```

`audit.py` is reusable: it checks both count endpoints, both rules, Racket labels,
the 22 finite hypotheses, matched inputs and private-invariant one-query exports.
It reports failures and refuses an existing output directory. The native source
inventory must be current before qualification. After integration, the owner
must qualify and accept the exact live source. This return grants no acceptance
or training admission.
