# Decisions for 537b409b6744 — review-149abe63a1c3c16f

The pinned selected v4.0.0 source and notes from return
`review-84d80652cf29f872:v0001` were used as leads only. Every claim below was
remeasured on this packet's selected baseline and final source.

## D1 / R1 — validate invocation scalars before constructing `gen_ctx`

**Prior choice.** v4.0.0 delegated `seed`, `sample_index`, and `difficulty` to the
context without an explicit type/domain guard.

**Decision.** v4.1.0 accepts only literal integer seeds, literal nonnegative
integer sample indices, and `None|easy|medium|hard` difficulty values. Booleans
are rejected even though Python treats them as integers.

**Alternatives rejected.** Coercing strings/floats would hide caller defects;
letting `gen_ctx` normalize them left the public contract inconsistent and caused
48 final-policy warnings. Restricting public generation axes was unnecessary.

**Evidence and failure modes.** The before defect-lint log records all 48 accepted
invalid values; the after battery and direct tests are green. This decision does
not define a maximum seed/sample index, and it does not change valid deterministic
recipes.

## D2 / R2 — declare `smallest_mover` as the canonical-fitting shortcut

**Prior choice.** v4.0.0 declared `CANONICAL_SHORTCUTS = {}` because its two
existing rivals (`farthest_pair`, `no_wall_growth`) were already refuted by some
canonical labels.

**Decision.** Add a separately executable rival that chooses the qualifying
candidate with minimum mover area and then uses canonical rank as the tie-break.
It is declared as a canonical shortcut and lesson competitor because it matches
all 8 usable canonical labels.

**Alternatives rejected.** Describing the ambiguity only in prose would leave the
semantic gate unable to test it. Treating “smallest” as equivalent to “nearest”
would be false on the retained area-4/gap-1 versus area-2/gap-3 witness.

**Evidence and limits.** `checks/shortcut/smallest-mover-evidence.json` binds the
final generator, canonical Racket bytes, independent probe, replay recipe, input,
Racket output, and rival output. The claim is exact for the 8 labeled pairs and
one counterexample; it is not a complete enumeration of all possible shortcuts.

## D3 / R2 — make every ordinary four-pair lesson refute the shortcut

**Prior choice.** Mover depth was randomly 1 or 2. A complete lesson could contain
only depth-1 nearest movers, making “smallest mover” observationally identical.

**Decision.** Use depth 2 on even default sample indices and depth 1 on odd ones;
retain the existing alternating solid/ragged distractor schedule. Explicit
`mover_depth` overrides still have the full 1..2 domain in every band. This makes
at least one larger-near/smaller-far input occur in every four consecutive
accepted draws, so every one-query rotation keeps a distinguishing demonstration.

**Alternatives rejected.** Forcing depth 2 on every input would unnecessarily
narrow the shape distribution. Rejection sampling until a witness appears would
make accepted indices less transparent. Adding a fourth demonstration would
change the production lesson contract.

**Evidence and limits.** Task tests enumerate all four schedule starts and all
held-out query positions. The large census materialized 300 three-demo/one-query
lessons and 1,200 rotations with zero declared-rival ambiguity. This proves the
bounded schedule property tested, not universal identifiability.

## D4 / P1 — prototype `candidate_selection=nearest|farthest`

**Decision.** The original family supports a small meaningful rule parameter:
which gap extremum wins. `nearest` is the canonical/default setting; `farthest`
changes only candidate ranking. The setting is selected once per episode and the
same Racket program labels all three demonstrations and one query.

**Alternatives rejected.** Varying colors, dimensions, direction, or gap would
change inputs rather than the executed rule. Varying wall growth would also be
valid but would duplicate an already-declared rival and provide less direct
coverage of the family's central candidate-selection reasoning.

**Evidence and limits.** The manifest contains two settings, two complete
Racket-labeled episodes, 16 executions, and six distinguishing demonstrations.
The prototype remains in `workspace/parametric/`; production `generate`, catalog
metadata, and selected authority do not expose a parametric API.

## D5 — preserve the selected Racket authority

**Decision.** Do not edit canonical/shared solution files and keep
`RULE_HASH=7b81cecb3b71`. The repair is entirely in the selected generator's Python
validation, distribution, declarations, tests, counterexample, probe, and
separate prototype.

**Reason.** The canonical transformation was not defective. Both the before and
after authority/rule-smoke stages showed the selected source and outputs bound to
the same authority. Changing it would conflate teaching repair with rule design.

## D6 — keep independent reusable probes

`workspace/reference_probe.py` now mirrors the smallest-mover rival independently
from production code. `checks/materialize_smallest_mover.py` materializes the
exact source-bound witness. The parametric prototype owns its Racket programs and
public/private episode split. These tools are retained so future agents can
recheck semantics without reverse-engineering the generator or exposing answers
inside public challenges.

## D7 — stop at a bounded canonical repair

No unrelated shared runtime, catalog, approval, or audit-target source was edited.
Audit findings for `f563fafba6ac` and `64a8d13b4024` remain findings-only. Remaining
unknowns are undeclared rival completeness and broader canonical geometry outside
the sampled helpful domain; both are reported rather than silently claimed away.
