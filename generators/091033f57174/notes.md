# Current notes: 091033f57174

## Intended rule

The canonical Racket program is authoritative (`RULE_HASH = 0ce03c4c47d8`). Cell `(0,0)` is command 1 or 2. For each other color occurring exactly twice, row-major-sort the endpoints and draw an L: command 1 uses the first endpoint's row then the second endpoint's column; command 2 uses the first endpoint's column then the second endpoint's row. Colors with counts other than two, including extra command-color cells, remain unchanged. The authority was not edited in this review.

## Selected generator: version 3.0.0

- Exact public product: `grid_h=8..12`, `grid_w=8..12`, `n_pairs=1..4`, `command=1|2`, and `texture=plain|three_cells|cmd_color_pair|both`.
- Unknown axes, invalid difficulties, implicit type coercions, and out-of-range values fail loudly.
- Explicit overrides are band-independent and observed after construction.
- Default lessons use a four-slot schedule with three demonstrations: command-1/plain canonical profile; command-2/plain canonical profile; command-1/three-pair/both-guards crossing; command-2/four-pair/both-guards crossing.
- Quadrant construction covers the full override product. Scheduled guarded slots use a finite crossing construction with guard cells outside canonical routes.
- `self_check`, `strict_canonical_like`, and `observe_overrides` share one structural analysis.
- Five executable rivals and five witnesses cover command orientation, exact count, whole-command-color exclusion, and processing all endpoint pairs.

## Reversed prior decisions

Version 2.1.1 used random commands/textures, difficulty-specific hidden ranges, permissive override parsing, and no source-bound semantic lesson contract. Direct probes found accepted typos/coercions and four-pair windows where a command-constant rival survived every demonstration. Version 3 replaces randomness with an enumerable curriculum and a truthful exact API. Evidence: `../../../checks/baseline-probe.txt`, `../../../checks/exhaustive-schedule.json`, and `../../../checks/lesson-census.json` in the review packet.

## Verification snapshot

Final generator SHA-256: `423a2879196b4b5ed2b4f51276c3ebcf4f63da503695c51d3579fb94ab26bfeb`.

- Portable focused suite: 66/66.
- Full after battery: 12/12 green.
- Full joint override product: 3,200/3,200 accepted and exactly observed.
- Exhaustive schedule: 16 lessons, 64 rotations, zero declared-rival ambiguities.
- Source-bound census: 300 lessons and 1,200 rotations, zero declared-rival ambiguities, 1,200 unique inputs.
- All five canonical inputs pass strict validation; canonical profile support is nonzero in every band.

## Known limits and open findings

The generated grammar is a strict training subset of all grids on which the Racket program can run. The guarded crossing schedule is finite. The declared-rival result is not universal identifiability, and no dedicated rival currently isolates alternate crossing overwrite precedence. The Python mirror is check-only; production labels must continue to come from Racket. Training admission remains unapproved pending maintainer intake.
## Current reviewer considerations

Source SHA-256: `423a2879196b4b5ed2b4f51276c3ebcf4f63da503695c51d3579fb94ab26bfeb`.

# Decisions: 091033f57174

## Authority and scope

The canonical Racket row is the label authority. Its normalized rule hash is `0ce03c4c47d8`; it was not edited. The repair changes only the selected generator package: implementation, current notes/summary, tests, workspace probes, and one retained counterexample. Audit targets `8af64ebfaf77` and `ad52210ad00d` were inspected only and remain unchanged.

`evidence/associated_notes.jsonl` was empty, so no prior return supplied a usable design lead. The pinned v2.1.1 source, canonical examples, before checks, and direct probes were the primary evidence.

## Intended transformation

Cell `(0,0)` is command color 1 or 2. For every other color occurring exactly twice, sort its two cells in row-major order. Command 1 draws the horizontal leg from the first endpoint to the second endpoint's column, then the vertical leg. Command 2 draws the vertical leg first, then the horizontal leg. Colors occurring any number other than two—including extra cells of the command color—are unchanged. Repeated pair painting follows the canonical color-discovery order, so crossings retain the authority's overwrite behavior.

## D1 — Replace permissive controls with an exact contract

**Prior choice:** v2.1.1 exposed controls whose documented ranges disagreed with hidden difficulty-band bounds. It accepted unknown keys and coerced floats/numeric strings. Invalid texture strings silently behaved like an unguarded texture.

**Selected choice:** expose only five measurable controls:

| Axis | Exact domain | Observation |
|---|---:|---|
| `grid_h` | integers 8–12 | row count |
| `grid_w` | integers 8–12 | column count |
| `n_pairs` | integers 1–4 | non-command colors occurring exactly twice |
| `command` | integer 1 or 2 | value at `(0,0)` |
| `texture` | `plain`, `three_cells`, `cmd_color_pair`, `both` | presence of a three-cell guard and/or two extra command-color cells |

Unknown keys, unknown difficulties, booleans, floats, numeric strings, and out-of-range values fail before generation. Any explicit override switches to the full product; unspecified axes are sampled from their full declared range and no difficulty band rewrites explicit values.

**Evidence:** `checks/baseline-probe.txt`, `checks/exact-domain.json`, and focused tests `test_exact_overrides_are_constructive_observable_and_band_independent` / `test_invalid_and_unknown_overrides_fail_loudly`.

**Rejected alternative:** keep the old broad ranges and declare many band-dependent incompatibilities. That would preserve a misleading API and require a large, fragile incompatibility table. A smaller truthful domain supplies enough geometric room for four pairs and two independent guards.

## D2 — Construct layouts instead of retrying

**Selected choice:** arbitrary override calls use four disjoint row/column regions, one endpoint pair per region. This deterministically supports 1–4 pairs on every 8–12 by 8–12 grid. Scheduled guarded examples use a fixed family of crossing arrangements on grids at least 10 by 10. Guard cells are selected only outside canonical pair paths, with a reserved zero proving that a shortcut would visibly change the output.

**Reason:** constructive placement makes the exact product total and lets `observe_overrides` equal the request by construction. It also avoids distribution shifts caused by retry exhaustion.

**Rejected alternative:** sample arbitrary endpoint pairs and retry on collisions. That made small/high-density corners difficult to reason about and could bias or truncate the advertised domain.

## D3 — Four-slot curriculum with three demonstrations

`EXAMPLES_NEEDED=3` and `LESSON_SCHEDULE_PERIOD=4`. In order, the default slots are:

1. command 1, two endpoint pairs, plain texture, a canonical input dimension;
2. command 2, two endpoint pairs, plain texture, a canonical input dimension;
3. command 1, three endpoint pairs, both guards, forced crossing;
4. command 2, four endpoint pairs, both guards, forced crossing.

Production assembly uses three demonstrations followed by one query in sample order. The design is stronger than that ordered requirement: deleting any one slot still leaves both bend commands in the demonstrations, at least one guarded example, and an example with at least three endpoint pairs. Therefore every query rotation refutes all five declared competitors.

**Prior choice:** commands and textures were random. The retained baseline probe found windows such as `[1,1,1,2]`; holding out command 2 leaves an always-command-1 rival perfectly consistent with every demo.

**Rejected alternative:** resample a random four-pair lesson until `lesson_identifiable` passes. Resampling hides the curriculum policy, complicates provenance, and does not guarantee every cyclic start. A deterministic schedule is cheaper to enumerate and audit.

**Evidence:** `checks/exhaustive-schedule.json` checks four bands × four starts and all 64 holdouts; `checks/lesson-census.json` checks 300 production lessons and 1,200 rotations.

## D4 — Preserve canonical profiles without replaying canonical placements

Slots 0 and 1 choose among the five canonical dimensions `(8,8)`, `(9,9)`, `(10,10)`, `(8,10)`, `(9,10)` and use two endpoint pairs with a plain texture. This preserves the canonical `(height,width,nonzero-count)` profiles while generating new placements and colors. Guarded slots expand to 10–12 dimensions for room.

The final profile-floor report has 30 exact hits in 60 draws and at least nine exact hits in every difficulty band. All five canonical inputs pass the strict validator.

**Rejected alternative:** replay canonical grids or fixed canonical endpoint positions. That would inflate profile metrics without improving generalization.

## D5 — Exact-count and command-color guards

The canonical examples alone permit at least three shortcuts:

- route any non-command color with two **or more** cells;
- exclude only the command cell `(0,0)`, then route the two remaining command-color cells;
- process only the first two endpoint-pair colors.

The `both` texture adds one non-command color occurring exactly three times and two extra cells of the command color. Neither lies on any canonical route. Scheduled guarded examples have 3 or 4 real endpoint pairs. Each guard reserves a zero on the corresponding shortcut route so disagreement is observable rather than merely structural.

The retained `counterexamples/guard-shortcuts.json` stores the exact input, canonical mirror output, rival outputs, source hash, and witness observations used by the regression suite.

## D6 — Semantic contract and independent checks

Five pure competitors are declared:

- `always_command_one`;
- `always_command_two`;
- `route_three_marker_colors`;
- `exclude_command_cell_only`;
- `first_two_pairs_only`.

Five witnesses correspond to those behaviors. `lesson_identifiable` first checks every supplied label against an independent Python mirror, then reports any competitor that fits all demonstrations but changes the query. The real Racket implementation remains authority; the mirror is a check oracle, not a replacement label source.

Task-local tests use portable `reviewer_support` helpers for all five canonical pairs. `workspace/reference_probe.py` is an independent geometry implementation; `workspace/domain_probe.py` enumerates the full joint control product; `workspace/schedule_probe.py` reads the generator's actual rival declarations and exhausts cyclic starts.

## D7 — Strict validator

`self_check` / `strict_canonical_like` now reject ragged grids, non-integer or out-of-range colors, invalid dimensions, missing/extra row-zero markers, reused non-command cue colors, endpoint counts outside 1–4, aligned endpoint pairs, guards on canonical routes, and guards without a visible shortcut route. Tests mutate valid inputs one defect at a time.

The validator intentionally accepts both canonical plain inputs and the guarded generated grammar. It does not claim to characterize every lawful input to the general Racket function.

## D8 — Solve evidence

The blind solve for `b39674306606` was completed before opening repair material. After the generator source was final, a new `091033f57174` visible-only episode was prepared. The post-repair solver inferred the command-selected exact-count L routing and passed 3/3 visible examples on revision 1. Because the rule had been seen during repair, `earlier_rule_exposure=yes`; `reference_consulted_during_solve=no` records that neither the Racket source nor generator was reopened during that solve.

## Limitations

- Zero ambiguity is only with respect to the five executable declared rivals.
- The full control-product probe tests one deterministic seed/sample per product point per band; the battery/census provide wider stochastic coverage but do not enumerate all seeds.
- Crossing schedule layouts are a finite constructive family. Explicit override layouts are broader, but neither spans every canonical-lawful geometry.
- Painting-order behavior is preserved and tested indirectly through Racket parity; no separate rival currently targets alternative overlap precedence.
- Training approval remains a maintainer decision; this return reports source-bound evidence only.
