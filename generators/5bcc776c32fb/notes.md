# Working notes: 5bcc776c32fb

## 2026-10-07 review repair

The pinned `2.1.0` baseline advertised nine controls but ordinary generation
materially used only dimensions. It omitted the canonical third input color,
accepted unknown controls, lacked `RULE_HASH`, and had no executable lesson
contract for several rules that fit all canonical demonstrations.

Version `3.1.0` replaces that metadata/implementation mismatch with four exact
round-tripping controls and a deterministic three-profile curriculum. The first
all-negatives draft was intentionally retained as failed evidence because it
produced 6--7 objects while canonical inputs center around 3. The final profiles
use 4--6 objects and distribute the negatives across lessons instead.

The canonical Racket program was not changed. Final evidence is under
`checks/after`, `checks/task-tests`, `checks/required-rotations`,
`checks/lesson-census.json`, and `checks/reference-probe.json` in the review
return. The independent probe and regression suite live in `workspace/` and
`tests/` respectively.
## Current reviewer considerations

Source SHA-256: `3aa97adf5be5f529c2ef3f451002e8622e4cefb9b45180dec005691e17b0ae90`.

# Decisions for 5bcc776c32fb

## Finding traceability

- **R1** drove the exact four-axis interface and removal of dead metadata.
- **R2** drove the three-profile schedule, length-9 positive, witnesses, and rivals.
- **R3** drove the split curriculum after the retained all-negatives attempt failed canonical object-count coverage.
- **A1/A2** are audit-only findings; no design or source change was made to those tasks.

## Design target

The selected Racket rule marks the midpoint of each color-1, single-row,
4-connected object whose size is odd and at least 3. The repair therefore had
two goals: generate inputs inside the canonical morphology/palette envelope and
make every logical clause inferable from a three-demonstration lesson. The
canonical Racket authority was kept unchanged because rule smoke and canonical
outputs were already correct.

No prior return ZIP was used as a design lead. I started from the pinned source,
its retained notes, canonical pairs, and the required before battery.

## Input controls

| Choice | Final decision | Original rationale | Alternatives considered | Probe / failure mode |
|---|---|---|---|---|
| `grid_h` | Exact integer `8..10` | Baseline allowed `6..18`; the reason for that broad range is unknown. | Keep the broad range; advertise only generated subranges. | Broad dimensions drifted from canonical support. Final defaults hit the canonical profiles `8x10`, `8x11`, `9x12`, and `10x13`; exact overrides are round-tripped. |
| `grid_w` | Exact integer `10..13` | Baseline allowed `8..20`; rationale unknown. | Independent full Cartesian dimensions. | Defaults condition width on height to stay on canonical profiles, while explicit overrides remain independent and exact. |
| `n_targets` | Exact integer `1..2` | Baseline exposed `n_lines=2..4` but did not honor it. | Count all line-like objects; omit a count axis. | Counting all lines would conflate targets with negatives. `observe_overrides` counts only qualifying blue objects and tests every legal value. |
| `distractor_color` | One exact color from `4,5,6,7,9` | Baseline advertised palette controls but ordinary draws were effectively `{0,1}`. | Random multi-color palettes; color permutations including 2. | The canonical task fixes blue as source and 2 as output, so those roles are not interchangeable. Exactly one non-rule color makes the control observable and restores canonical palette size 3 without prepainting output color 2. |
| Removed controls | Delete `palette_kind`, `palette_size`, `n_distinct_colors`, `position_bias`, `density`, `texture`, and degenerate aliases. | Original rationale is not documented; most were dead, overlapping, or not observable. | Keep metadata and special-case every override. | Before override testing reported 18,986 findings, 37,530 undeclared rejections, and accepted unknown keys. A smaller truthful interface is safer than simulated combinatorics. |

Unknown keys, booleans passed as integers, out-of-domain values, and invalid
difficulty names now fail explicitly. There are no declared incompatible
combinations because all four controls can be honored jointly.

## Scene grammar

Every scene starts from a canonical-scale `8x10` layout, then may be reflected
and embedded in the selected dimensions. It always contains one or two genuine
blue targets, including a length-9 target. Length 9 is outside the canonical
positive set `{3,5,7}`, so it directly rejects a learner that memorizes observed
lengths instead of the odd-length rule.

The other negatives are distributed over a deterministic period-3 schedule:

1. `parity_orientation_shape`: even horizontal blue object, odd vertical blue
   object, bent blue object with an odd row run, and a benign one-cell distractor.
2. `minimum_color_shape`: blue singleton, bent blue object, and a non-blue odd
   horizontal line.
3. `minimum_color_parity_orientation`: even horizontal, odd vertical, blue
   singleton, and non-blue odd horizontal line.

A lesson uses three demonstrations and one query. Any held-out position leaves
two profile types among the demonstrations; every pair of profile types jointly
refutes all six declared competitors: color-blind, no-minimum, lengths-3/5/7,
parity-blind, orientation-blind, and row-run-without-components. The production
census uses consecutive schedule starts and required query rotation.

### Rejected scene alternatives

- **Put every negative in every grid.** The first repair attempt was semantically
  strong but produced 6--7 objects per scene. The defect detector rejected this
  because canonical object count centers around 3. That failed run is retained
  under `checks/after-attempt1`. The final split curriculum yields 4--6 objects.
- **Choose witnesses independently at random.** This can create individually
  valid grids but an ambiguous lesson when a query-relevant witness is absent
  from all demonstrations. The period-3 schedule makes lesson coverage a
  structural property rather than a frequency claim.
- **Use only canonical positive lengths.** This preserves superficial realism
  but leaves the `lengths_357` rival indistinguishable. Length 9 is required in
  every scene.
- **Change the Racket rule.** Rejected: the authority matched all canonical
  outputs and passed source synchronization. The defect was input distribution
  and curriculum, not labels.

## Validation and semantic contract

`self_check` validates the broad lawful grammar without consulting labels.
`strict_canonical_like` adds canonical dimensions, three-color palette, and at
least one non-target blue object. `observe_overrides` independently reconstructs
all four public controls from the returned grid. Generation checks both hooks
before returning.

The Python `rule_mirror` is test/probe support only. Canonical Racket remains the
authority. Six executable rivals and seven witness predicates are declared, and
`lesson_identifiable` only requires a rival to be refuted when it predicts the
query incorrectly. This avoids rejecting harmless rival equivalence on a
particular query.

The independent `workspace/reference_probe.py` reimplements components, rule,
rivals, and observations rather than importing these semantic helpers. It also
checks a source-color counterexample against real Racket.

## Testing choices

The task-local suite covers:

- canonical oracle agreement and real-Racket parity;
- all legal exact override values and invalid override behavior;
- deterministic generation and global-RNG isolation;
- canonical profile coverage and object-count bounds;
- each witness and each declared rival;
- all cyclic starts/query positions of the period-3 curriculum;
- malformed grids and validator behavior;
- the independent probe itself.

The final portable task-test run passed 103/103. The full battery passed 12/12.
The required-rotation semantic stage passed, the shared census found 0 ambiguous
production lessons out of 300 and 0 ambiguous query rotations out of 1,200, and
the independent probe found 0 ambiguous local rotations out of 192.

## Known limits

- Identifiability is measured against six named, executable rivals. It is not a
  proof against every possible human or program hypothesis.
- The scene grammar intentionally prioritizes clause coverage over reproducing
  every canonical spatial arrangement. It is bounded to four canonical
  dimension profiles, one distractor color per input, and 4--6 objects.
- The period-3 schedule is part of the curriculum contract. The required
  rotation checks show any one of four materialized pairs can be the query, but
  do not certify arbitrary lesson assemblers that discard or reorder more than
  one pair.
- Difficulty changes the optional second target length, not the number or type
  of semantic clauses. This is deliberate: difficulty must not remove evidence
  needed to infer the rule.
