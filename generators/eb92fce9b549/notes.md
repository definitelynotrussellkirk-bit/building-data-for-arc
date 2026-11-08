# Working notes: eb92fce9b549

## Review handoff (2026-10-02)

- Original generator SHA-256: `75f8644447f0c190d81c427758aa289dd6242fa5fd6b8d6fedcb525c42de9f70`.
- Final generator SHA-256: `233751e50f0534ff225c8d74cc35ed1cb939755d6cc006f201269f6556a1dceb`.
- Canonical Racket authority was not edited; pinned rule hash is `45c25a11961c`.
- Original source is retained at `workspace/history/generator-v2.2.0-original.py`.
- Independent geometry/oracle helper: `workspace/reference_probe.py`.
- Long-run real-runner/Racket lesson census: `workspace/semantic_probe.py`.
- Regression suite: `tests/test_generator_review.py`.
- Final official battery: 12/12 green under `checks/final-verify-battery/` in the review return.
- Long-run census: 300/300 identifiable lessons, 1,037 unique inputs across 1,200 pairs, zero errors, and 798 cell-count-rival disagreements.

The deliberate domain is narrower than the imported source: square 7–24 grids, one foreground color, 2–4 objects, and unique bounding-box areas. The strongest declared canonical-fitting rival is occupied-cell-count ranking.
## Current reviewer considerations

Source SHA-256: `233751e50f0534ff225c8d74cc35ed1cb939755d6cc006f201269f6556a1dceb`.

# Decisions: eb92fce9b549

The original task-local notes contained no rationale beyond an empty working-note template, so original design intent is **unknown** except where it can be inferred from source. The decisions below describe the replacement and the evidence that motivated it.

## D1 — Preserve the authority; repair only the curriculum

The canonical Racket rule already produced all canonical outputs and passed baseline rule smoke/authority sync. I therefore left it byte-for-byte unchanged and pinned `RULE_HASH = "45c25a11961c"` in the generator. Changing the rule would have increased risk without addressing G1 or G2.

**Rejected alternative:** modify the authority to rank by occupied-cell count. That would fit the public frames but change the intended task and contradict the existing canonical program.

## D2 — Replace the broad, dishonest axis surface with four exact controls (G1)

The original `grid_h`, `grid_w`, `n_blobs`, `blob_size`, `palette_size`, `position_bias`, and `texture` surface was not an exact contract: dimensions were often ignored, helpful textures were dead, negative textures overlapped the ordinary domain, and unknown keys were accepted. I replaced it with:

| Axis | Exact domain | Distribution choice | Why |
|---|---|---|---|
| `grid_size` | integer 7–24 | Default sizes are 7, 9, 11, 13, 15. | Square grids match every canonical profile; the broader exact range remains useful for stress testing. |
| `n_objects` | integer 2–4 | Difficulty-aware weighting. | Enough ranks to teach ordering without fragile packing or output colors beyond the task's demonstrated range. |
| `layout` | `rings` or `scattered` | Deterministic `rings, scattered, scattered` schedule by sample index. | Preserves canonical appearance while guaranteeing shortcut-breaking lessons. |
| `foreground_color` | integer 1–9 | Uniform nonzero ARC color. | Canonical inputs use a single foreground color; color should not leak rank. |

Every axis is recoverable from pixels through `observe_overrides`. Unknown keys and wrong types fail loudly.

**Rejected alternatives:** retain compatibility aliases for the old axes; keep decorative `palette_kind`/`texture` controls; or silently coerce invalid requests. Those choices would preserve the defect rather than the useful task domain.

## D3 — Use a canonical ring family plus a constructive semantic witness family (G2)

### Rings

The ring branch draws 2–4 same-color rectangular perimeters, each inset by two cells. The extra cell between adjacent perimeters is a blank moat, so 4-connectivity produces separate objects. Rings retain the canonical visual family and make bounding-box rank obvious.

### Scattered witness

The scattered branch starts from a 7×7 motif with component statistics:

1. sparse L: bounding-box area 9, cell count 5;
2. dense rectangle: bounding-box area 6, cell count 6;
3. line: bounding-box area 4, cell count 4;
4. domino: bounding-box area 2, cell count 2.

The first two objects reverse order under cell-count ranking. A D4 transform and lawful translation vary appearance without weakening the witness. Truncating to any allowed `n_objects` still retains the first two and therefore the disagreement.

**Rejected alternatives:** random walks with post-hoc rejection, because they made witness frequency probabilistic; all-rings curricula, because they never distinguish perimeter cell count from bounding-box area; or arbitrary multicolor blobs, because color could become an unintended ranking cue.

## D4 — Make complete lessons identifiable, not merely individual samples (G2)

The default layout schedule is periodic with period three: one ring followed by two scattered witnesses. `EXAMPLES_NEEDED = 3`, and `lesson_identifiable` explicitly checks the declared `cell_count_rank` competitor against the demos. The test suite checks all starts 0–23 in every difficulty band, rather than checking witness frequency alone. The long-run probe then uses the actual shared lesson assembler for 100 lessons per band.

**Rejected alternative:** independent random layout choice. Even a high witness rate leaves a nonzero chance that all demonstrations support the shortcut.

## D5 — Keep canonical profiles in every difficulty band (G4)

All default sizes come from the five canonical square side lengths. Difficulty changes weights and object-count preferences, not the support set. This yields exact canonical shape/palette profiles in each band while still varying geometry, position, transform, color, and count.

**Rejected alternative:** large hard-only grids. The baseline did that and produced zero hard-band canonical-profile support.

## D6 — Declare only real incompatibilities

Same-color nested rings need an outer side of at least `4*(n_objects-1)+1`. The generator declares the eight impossible exact triples and raises a structured `ValueError` containing the responsible axes. All other advertised combinations are constructive.

For partial overrides, unpinned choices adapt. Example: `layout=rings, grid_size=7` chooses 2 objects even in the hard band; `grid_size=7, n_objects=4` selects scattered when layout is unpinned. This decision was added only after the retained intermediate battery exposed G3.

**Rejected alternative:** reject every partial request that conflicts with the current difficulty weighting. Difficulty is a preference, while exact user overrides are the contract.

## D7 — Validate the task manifold directly

`self_check` now verifies rectangularity, square side 7–24, integer ARC colors, 2–4 same-color 4-connected components, and unique bounding-box areas. `strict_canonical_like` uses this same lawful domain. Equal-area examples are intentionally excluded because the authority has no declared tie semantics in the public task.

**Limitation:** this intentionally narrows the old claim of “2–8 arbitrary blobs.” It is a smaller domain with stronger guarantees, not a universal ARC object generator.

## D8 — Declare the actual ambiguity and counterexample hooks

The generator exposes the same `cell_count_rank` callable through `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, with `bbox_vs_cell_count` as its witness. The callable is pure and does not mutate inputs. The official semantic gate confirmed that the rival fits all five canonical pairs and that generated witnesses refute it.

**Rejected alternative:** merely describe the rival in prose. Executable declarations let the battery and future probes detect regressions.

## D9 — Build reusable independent probes

- `workspace/reference_probe.py` independently implements 4-connected components, bounding boxes, intended/rival outputs, canonical loading, and observed-axis recovery.
- `workspace/semantic_probe.py` runs the actual shared runner and Racket bridge, reads declared competitors from the generator, binds reports to source SHA-256 values, and records 100+ lessons per band, uniqueness, strictness, profiles, witnesses, and lesson identifiability.

These tools avoid validating the sampler solely with its own helper functions.

## D10 — Preserve failures and state the evidence boundary

The original generator is retained in `workspace/history/`. The failed hard/7×7 intermediate battery is retained under `checks/after-failed-hard-small/`. The long-run result is reported as a sampled census, not proof that every possible solver learns the intended abstraction. The fresh solve was stopped after one passing visible-example revision; masked correctness remains unknown.
