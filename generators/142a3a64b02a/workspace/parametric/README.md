# Native whole-component caps / residual-largest family

`adapter.py` provides `program(settings)` and `generate(seed, settings, demos,
queries)`. `promotion.json` declares `mode=caps|residual_largest`, 2–6 demos,
1–4 prefix-stable queries, and a two-demo qualification minimum. Store four
queries privately, then use the existing packet sequential preview/shuffler.
No controller, training loop, or acceptance is implemented here.

## Rule and causal dependency

`caps` reads the exact selected canonical Racket bytes. It caps the two extrema
of each wholly straight red 4-connected component with yellow 4. Other red
components and all non-red cells remain unchanged. A singleton is capped once;
a length-two segment loses all its red cells. These branches are not removed.

`residual_largest` executes those caps, recomputes the remaining red components,
then recolors the largest one to cyan 8. Equal sizes choose row-major first.
The intermediate is the post-capping component's cell set and size. A formerly
largest straight component can shrink below a non-straight competitor, so B
cannot use pre-capping sizes. `wrong_intermediate.rkt` substitutes the largest
original red object while still preserving the correct caps; it recolors only
still-red cells of that wrong object. This isolates selection, not cap loss.
No remaining red component means no relay.

## Constructive lesson and broader grammar

Both minimum demonstrations contain horizontal AND vertical positives, a T and
an L, a diagonally touching but 4-disconnected red cycle, singletons, pairs,
a length-three line, and non-red objects. One demonstration makes the straight
object lose the size contest after capping; the other makes a straight interior
win. Same-size T/L objects and their different bounding-box areas expose tie,
connectivity and area shortcuts. The original source's orientation gap is
therefore excluded in this native curriculum, not merely checked after sampling.

A large non-red distractor in *every* demo originally concealed an all-color
selection shortcut under the plain `caps` setting. The second demo now makes
that distractor smaller than the winning red interior. This repairs both modes
without increasing the two-demo minimum. `regression/allcolor-before.json`
retains the old fitting lesson and separating query. The audit executes both
programs before and after the repair.

Independent RNG streams vary dimensions, component sizes, L orientations,
reflections, decoy palettes, and relative line lengths. First demos are no
longer a tiny fixed-dimension catalog: 32/32 distinct first demos were observed
in the retained 32-seed run. Inputs are identical across settings and count
changes preserve the input/output prefixes. Queries include an independently
sampled 30×30 scene with four boundary-spanning straight components plus 25
interior colored objects. These are substantive objects, not padding.

This separate grammar extends the production manifold to cycles, multiple
objects, length-one/two components, larger sizes and several non-red colors.
The reference rule supports them. Production `self_check`, sampling and authority
are deliberately untouched; its existing horizontal-only teaching finding
remains open. This native repair must not be used to close that production audit.

## Reproduce

From the packet outer directory:

```sh
python3 review.py run python3 generators/142a3a64b02a/workspace/parametric/audit.py --out ../checks/142a3a64b02a/audit-new.json
python3 review.py task-tests 142a3a64b02a --phase after --out ../checks/142a3a64b02a/tests-new
python3 review.py run python3 -m arcpuzzles parametric qualify 142a3a64b02a --out ../checks/142a3a64b02a/qualification-new --summary
```

Retained scope: 46 tests, 320 episodes over 32 seeds and all demo counts 2–6;
2,560 labeled-pair checks, 319 distinct inputs, 26 declared policies, no observed
finite-rival failures. The audit executed 66 protected-Racket labels, including
boundary/degenerate cases, the original production orientation ambiguity, and
the new before/after all-color regression. Most census labels are Python claims;
qualification independently executes every retained setting/job. Neither finite
rivals nor tested seeds prove universal uniqueness. Author self-review only;
no independent reviewer, owner acceptance, or training admission is claimed.
