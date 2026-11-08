# Working notes: 9bbc588810ae

## 2026-10-05 review repair

The imported 2.0.1 rewrite had the correct four-panel concept but no `RULE_HASH`, an interface with ignored/singleton axes, accepted unknown overrides, ordinary degenerate textures that failed self-check, no semantic contract, and no task-local regression tests. Its prose also claimed all eight dihedral transforms even though the frozen authority's `rot270` branch is another transpose.

Version 3.0.0 pins the authority and exposes only four exact, pixel-observable axes: `palette_kind`, `transform`, `match_panel`, and `query_cells`. It constructively enumerates 4-connected polyominoes, uses asymmetric queries, guarantees exactly one authority-supported match, and rejects unknown/invalid overrides before drawing.

The strongest plausible canonical-fitting rival found was: among source panels with the query's cell count and bounding-box dimensions up to swap, choose the lowest source color. It matches all three canonical pairs. The generator now always includes a same-signature non-dihedral decoy, and the scheduled `bbox_lower_color_witness` assigns that decoy a lower color than the real match. The initial three-cycle made normal ordered lessons identifiable but left some query rotations ambiguous; the retained failing census in `checks/lesson-census-attempt1-rotation-ambiguous.json` found 83/1,200 ambiguous rotations. The final four-cycle is witness/agree/witness/permuted, so any three of four consecutive labelled pairs contain a witness. The final census reports 0/300 production ambiguities and 0/1,200 rotated ambiguities against the declared rival.

The Racket authority and canonical data were not changed. See `workspace/probe_contract.py` for a reusable exact counterexample, canonical parity, coverage, and rotation probe. Associated imported notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `66973c55226bac3e9020b15321e4d80a45249b5228fe507c8e9cd3d207b80d73`.

# Decisions for `9bbc588810ae`

## Scope and source of truth

I treated the canonical Racket implementation selected by the packet as authoritative and left it unchanged. The repaired Python generator pins `RULE_HASH = "a63dd2ae1f7a"`; the final authority-sync and public-apply checks bind the source to that hash. No associated prior-return notes were present (`evidence/associated_notes.jsonl` is empty), so the immutable packet baseline and newly run checks—not prior claims—were the evidence for the repair.

The baseline generator appeared to be a previous rewrite aimed at the correct four-panel concept, but its original design rationale was not recoverable. I preserved the intended task family while replacing its untestable interface and malformed ordinary examples.

## D1 — Match the authority actually present, not an idealized dihedral group

The frozen authority names eight transformation branches, but its nominal `rot270` branch duplicates transpose. Therefore the exact source-to-query operations actually implemented are:

`id`, `r1`, `r2`, `fh`, `fv`, `tr`, `atr`.

I deliberately did **not** advertise `r3` as an exact axis. Advertising an operation that the authority cannot execute would make exact overrides dishonest and could generate labels that only an idealized rule, not the selected Racket code, would support. The generator still uses the full eight-operation geometric orbit internally when deciding whether a query is asymmetric and whether a decoy is truly non-dihedral; that is a shape-classification aid, not a claim about authority support.

Rejected alternative: change the Racket `rot270` branch. That would alter the reference rule and was unnecessary to repair the sampler. It would also require a new authority decision rather than a routine generator repair.

## D2 — Reduce the public axis surface to four exact, observable controls

The final `AXES` are:

- `palette_kind`: `default|warm|cool|varied`
- `transform`: `id|r1|r2|fh|fv|tr|atr`
- `match_panel`: integer `0..2`
- `query_cells`: integer `4..8`

Each can be recovered from returned pixels by `observe_axes`/`observe_overrides`; all legal values remain valid in every difficulty band. Unknown axes, wrong types (including `bool` for integer axes), retired axes, and out-of-range values reject before any draw.

This replaces the baseline's singleton/dead `palette_size`, `position_bias`, `n_distinct_colors`, and `density` axes plus the overloaded `texture` axis. The baseline advertised helpful textures that were byte-identical to defaults, silently accepted unknown keys, and mixed malformed negative fixtures into the ordinary valid domain.

Rejected alternative: keep compatibility aliases for retired axes. Silent compatibility would preserve the exact defect the override gate found. A loud error is safer for downstream curriculum code because stale or misspelled controls cannot masquerade as successful exact draws.

## D3 — Construct shapes rather than patch malformed cases

The generator enumerates fixed 4-connected polyominoes of 4–8 cells that fit a 5x5 panel. Query candidates must be asymmetric under the full geometric orbit and must have at least one same-cell-count, same-bounding-box non-dihedral peer. The matching source is created by applying the inverse of the selected authority-supported transform; its relation to the query is therefore constructive rather than accidental.

Every ordinary draw has:

1. one exact matching source;
2. one same-signature non-dihedral decoy;
3. one distractor with a different cell count;
4. one nonempty 4-connected query;
5. four distinct content colors plus the fixed color-9 dividers.

`self_check` independently parses the four panels, validates dimensions/dividers/colors/connectivity, and requires exactly one matching source. `rule_mirror` re-derives the answer from pixels rather than returning generation metadata.

Rejected alternative: retain `no_query`, `no_match`, or `two_matches` as ordinary textures. Those are useful mutation tests, not lawful training inputs. They now live in `mutation_fixtures()` and are expected to fail validation.

## D4 — Use exact palette families with color order independent of panel identity

The palette families are four distinct recoverable sets:

- `default`: `{1,2,3,4}`
- `warm`: `{2,4,7,8}`
- `cool`: `{1,3,5,6}`
- `varied`: `{2,3,6,8}`

The query and three source panels receive all four colors. The scheduled profile controls only their assignment, not geometry or correctness. The `permuted_colors` profile shuffles assignments so that panel index, source color, and query color do not become stable proxies for the rule.

Rejected alternative: sample arbitrary four-color subsets. That would increase superficial diversity but make an exact `palette_kind` override non-observable unless extra metadata were retained. The selected four sets give a clean pixel-level inverse for the override checker.

## D5 — Target the strongest canonical-fitting rival explicitly

The canonical demonstrations admit the plausible shortcut `bbox_count_lowest_color`: among source panels with the query's foreground count and bounding-box dimensions (allowing swapped height/width), choose the lowest source color. It fits all three canonical pairs because their signature peer with the lowest color is also the true match.

The repaired generator always includes a same-signature decoy. In profile `bbox_lower_color_witness`, that decoy receives the lowest source color while the true match receives a higher color. The intended rule and shortcut then predict identical masks but different colors, giving a compact and unambiguous teaching witness. In `bbox_match_low`, the match gets the lower color so the rival agrees; `permuted_colors` prevents a fixed color convention.

An exact witness, independently checked by public Racket application, is retained in `checks/contract-probe-final.json` and reproduced in `QUESTION_ANSWER.md`.

Limitation: this contract tests a named, executable rival that is strong and canonical-fitting. It does not prove uniqueness against all possible programs or natural-language hypotheses.

## D6 — Strengthen lesson scheduling after a real rotated-query failure

The first repaired schedule used a three-profile cycle. It made ordinary ordered three-demonstration lessons identifiable, but the required 300-lesson census found 83 ambiguous cases among 1,200 held-out query rotations: if the only decisive witness became the query, all remaining demonstrations could still fit the rival. I preserved that full failure in `checks/lesson-census-attempt1-rotation-ambiguous.json` and added a focused failing test in `checks/task-tests-rotation-red.log`.

The final four-sample cycle is:

`bbox_lower_color_witness`, `bbox_match_low`, `bbox_lower_color_witness`, `permuted_colors`.

Every three consecutive samples contain a witness. More importantly, any one of four consecutive labelled pairs can be held out as query and the remaining three still contain at least one witness. The task-local regression exhausts every query position for overlapping four-pair windows across bands, seeds, and starts. The final census found 0/300 production ambiguities and 0/1,200 rotated ambiguities against the declared rival.

Rejected alternative: merely document the ordered-curriculum limitation. The downstream diagnostic explicitly allows query rotation, and the stronger schedule costs only one extra repeated witness per four draws while keeping all three named profile behaviors.

## D7 — Difficulty changes weights, never legal support

Difficulty affects only default sampling weights for `query_cells`:

- easy favors 4–5 cells;
- medium favors 5–7 cells;
- hard favors 7–8 cells;
- unspecified is uniform over 4–8.

Every legal exact override is accepted in every band. Non-axis random draw labels include the band so equal axis values do not collapse easy, medium, and hard into byte-identical geometry. No difficulty-specific validity restriction is hidden behind the public axis declaration.

Rejected alternative: narrow the legal cell-count range by band. That would recreate the audit defect seen in `55c08ab3ce73`, where an advertised global range rejects under an easy route.

## D8 — Tests and evidence are source-bound

I wrote tests before implementing the repair. Against the baseline, the initial suite produced 56 failures and 10 passes (`checks/task-tests-red.log`), covering missing rule pin/observers, ignored and unknown overrides, absent semantic hooks, and missing mirrors. After the first implementation, 66 tests passed; the lesson census then exposed the rotation defect, and a new single-test red run captured it before the schedule change. The final selected-task stage reports 67/67 passing from generator SHA-256 `66973c55226bac3e9020b15321e4d80a45249b5228fe507c8e9cd3d207b80d73`.

`workspace/probe_contract.py` is intentionally reusable by future agents. It independently checks canonical parity, exact axis coverage, 120 generated draws, overlapping four-pair query rotations, and the first generated rival counterexample. Optional `--racket` mode calls public `Catalog.apply` and records both generator and rule hashes. The final receipt is `checks/contract-probe-final.json`.

## D9 — Self-review for new shortcuts and restrictions

The constructive decoy could itself have created a new shortcut if its panel, color rank, or profile position were fixed. Panel placement is drawn independently, match panel is an exact full-support axis, palettes vary, and the permuted profile breaks stable color ordering. The 120-draw contract probe covered all seven transforms, all three match panels, all five cell counts, all four palettes, 120 unique inputs, and 119 unique outputs.

The intentional distribution restriction is that query shapes are asymmetric 4–8-cell polyominoes with an available same-signature non-dihedral decoy. Symmetric shapes, cell counts outside 4–8, malformed panels, and the authority-missing true `r3` operation are not trained. These restrictions are explicit in `SUMMARY.md`, invariants, axes, and tests rather than hidden sampler accidents.

## D10 — Reference, solve, and audit boundaries

The Racket authority and canonical data were not modified. The post-repair solve was prepared only after freezing final generator SHA-256 `66973...80d73`; while solving I used visible examples only, declared earlier rule exposure `yes`, and did not consult a reference. Revision 1 matched all three visible demonstrations; masked-query correctness remains withheld.

The mandatory pre-repair blind solve targeted the separate task `7e52d15790d7`, declared earlier exposure `no`, and also used one visible-example-consistent revision. Its unresolved equal-area tie-break uncertainty is retained rather than hidden.

The two audit targets were not edited. `55c08ab3ce73` has a reproduced support/override defect; `4c04ce6c5477` had no issue within its declared domain, with its out-of-domain tie/touching/multicolor behavior documented as a question rather than promoted to a defect.
