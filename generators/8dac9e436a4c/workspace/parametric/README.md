# Filled-area matching family — authoring plan and contract

Keep the approved generator and canonical frame-fill Racket exact. Add the
private episode setting `match_policy=fill_only|area_match`. The alternative
fills all hollow color-6 frames as before, selects the unique largest newly
created color-8 component, and recolors the separate solid color-6 rectangle
with the same occupied area to color 3. The payload deliberately has a different
aspect ratio from the filled region; a smaller filled region has its own solid
match, and a larger solid distractor defeats largest-solid selection.

Rejected alternatives: changing fill color (no state dependency), or always
recoloring the largest solid (ignores reconstructed frame interior). The selected
rule carries a measured input-dependent area from a reconstructed object to a
separate payload. No new training consumer or turn controller is built.

Implementation plan:
1. Failing literal tests for frame fill and remote area match, smaller-area
   counterfactual, exact canonical source, count/settings validation and masking.
2. Implement adapter and constructive shelf packing with multiple hollow/solid
   objects; preserve setting-neutral, count-independent inputs and shuffled
   four-query roles including substantial 30x30 content.
3. Self-review against executable rivals with two-demo teaching checks; run the
   task-local reusable audit, protected Racket parity and changed-target tests.
4. Freeze inventory, native qualify both settings, and retain a source-bound
   protected-Racket wrong-intermediate witness. Owner acceptance stays pending.

## Implemented surface and reproduction

The adapter supports independent 2–6 demos and 1–4 queries. A setting-independent
seed stream constructs six demos and four shuffled query roles, and requests
slice stable prefixes. The smallest 8x12 examples retain canonical scale; other
roles reach 30x30. The large query has five hollow frames and seven solid
rectangles, dispersed across the canvas and all four boundaries. Objects may
transpose and layouts may reflect; paint semantics and the role palette remain
fixed. The decoration is external and does not encode the setting.

The largest filled interior has one unique solid-area match of a different
aspect ratio. A smaller interior has its own match; larger and smaller solids
remain distractors. No equal-largest ambiguity is emitted. In the general
Racket expression all exact-area solid matches are recolored, but multiple
matching payloads and absent matches are not claimed as sampled curriculum.
Filled interiors remain 8; the matched solid alone becomes 3.

```sh
python3 review.py run python3 -m pytest generators/8dac9e436a4c/tests/test_parametric.py -q
python3 review.py run python3 generators/8dac9e436a4c/workspace/parametric/audit.py --seeds 20 --out ../checks/8dac9e436a4c/new-audit
python3 review.py run python3 ../checks/8dac9e436a4c/check_rank_regression.py
python3 review.py task-tests 8dac9e436a4c --phase after --out ../checks/8dac9e436a4c/new-tests
```

`audit.py` is a standalone copy of the same task-local audit interface used by
the first build; it imports only this directory's adapter. No sibling workspace,
predecessor checkout or nonlocal runtime is borrowed. It tests count boundaries,
setting-neutral inputs, stable prefixes, exact masking and public identifiers,
then executes selected and rival rules through protected Racket. Public files
contain one query only; all four labels/programs/settings remain in a private
bundle for the existing controller.

## Self-review finding and repair

The initial ordinary scenes had three solids: smaller, equal and larger than
the reconstructed interior. That made median/second-smallest/second-largest
area selection fit both initial demos while disagreeing on the seven-solid
30x30 query. A failing literal-rank regression reproduced the gap. The second
teaching scene now includes additional solids of areas 1, 10 and 12, making
the true six-cell target neither the median nor either second-ranked extreme.
No extra demonstration is needed. Protected before/after evidence, exact rival
programs, inputs and outputs are in `checks/8dac9e436a4c/rank-repair.protected.json`.
Its replay command executes 20 real Racket applications. The altered early
scene is included for every supported demo count.

The final finite bank also tests smallest/second filled region, largest/smallest/
first/last solid, dimension matching (including rotation), frame border count,
outer frame area, and first-frame-only filling. Every nonselected declared rule
is rejected by the first two visible demos; query labels are not used to fit
survivors. 800 count/setting requests over 20 seeds, including all supported
counts, completed without failures. These repeated prefix requests comprise
5,200 labeled-pair checks, not 5,200 independent random scenes.

Shelf packing is bounded (128 orders per layout and 128 layout attempts), uses
blank separation, and raises explicitly on failure. This is not uniform sampling
over legal scenes. Finite evidence is not universal uniqueness or measured
learning benefit. Review was by the author; owner exact-source acceptance and
any downstream training admission remain separate.
