# Working notes: 697e51dfedef

Version 2.0.0 replaces retry-based placement and dishonest singleton/dead axes with constructive three-slot placement and exact `grid_h`, `grid_w`, and `layout_order` controls. The canonical Racket authority is unchanged and pinned by `RULE_HASH = "5f4ba5cc9570"`.

The strongest canonical shortcut is reading-order recoloring. The six-profile schedule includes aligned and misaligned 8×8/9×9 anchors plus broad descending/scrambled cases, so every consecutive four-profile lesson window contains counterexamples. See `workspace/reference_probe.py` for the independent oracle, rival, exact witness, sampling audit, and optional Racket parity check.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `a1fdade971c483cf994c965a22be42f8de80b9242973a681d57c08a1b7f0e76b`.

# Decisions for `697e51dfedef`

## D1 — Preserve the canonical rule

**Choice.** Leave the selected Racket authority unchanged and pin `RULE_HASH = "5f4ba5cc9570"`.

**Rationale.** The canonical rule already consistently sorts the three objects by area and recolors ranks to 2, 4, and 8. Baseline rule-smoke and authority-sync checks were green; the defects were in sampling, metadata, and teaching support.

**Alternatives rejected.** Rewriting Racket would add an unnecessary authority change and risk changing canonical outputs. Treating the archival divergent raw source as selected authority was also rejected; authority-sync identifies it as archival only.

**Probe / failure mode.** Task tests compare all three canonical pairs to an independent Python oracle, and four cases are checked against actual Racket. Any future authority change must update the pin and rerun those checks.

## D2 — Expose only honest, observable axes

**Choice.** Public axes are `grid_h` in 7..14, `grid_w` in 7..14, and `layout_order` in `ascending|descending|scrambled`.

**Rationale.** These values alter returned pixels and can be recovered from the grid. Strict unknown-key and type rejection keeps the contract auditable.

**Alternatives rejected.** The baseline singleton axes (`n_blobs`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`) were invariants masquerading as controls. `palette_kind`/`texture` values were dead aliases, and negative fixtures such as `no_blobs` did not belong in the ordinary legal domain.

**Probe / failure mode.** The final override matrix exercised 132 cases × 3 bands × 30 seeds = 11,880 draws with zero mismatch or warning. Adding a future axis requires a real multi-valued pixel effect and an observation hook.

## D3 — Make three-object placement constructive

**Choice.** Select three of four separated corner slots and grow each object wholly within its own 3×3 slot.

**Rationale.** Construction, rather than capped retry, guarantees exactly three non-touching objects for every supported grid size and override.

**Alternatives rejected.** Retrying free placement can silently drop an object, especially near small dimensions. Raising after exhausted retries would be honest but unnecessarily nondeterministic and costly.

**Probe / failure mode.** Focused tests cover 512 samples per band; the independent probe covers another 200 per band. All had zero invalid or nondeterministic cases. The bounded slot size is a documented curriculum restriction, not a claim about the full Racket domain.

## D4 — Keep areas distinct and vary size rank independently of position

**Choice.** Draw three distinct areas, then map them to reading-order slots according to an explicit layout mode.

**Rationale.** Distinct areas avoid undefined tie behavior and directly teach the authoritative size ranking. Decoupling area from position creates counterexamples to the strongest canonical shortcut.

**Alternatives rejected.** Tied sizes, one object, and zero objects were negative fixtures that either fall outside the intended task or fail to teach the three-rank mapping. Always-ascending placement leaves reading order answer-equivalent.

**Probe / failure mode.** `observe_overrides` recovers layout mode from object sizes in reading order, and generation raises if the observed contract differs from the request.

## D5 — Use six teaching profiles

**Choice.** Cycle through canonical-size aligned and misaligned profiles plus broad descending/scrambled profiles.

**Rationale.** Canonical 8×8 and 9×9 anchors maintain morphology support, while non-ascending examples refute reading order. The cycle is chosen so every consecutive four-profile window includes at least two witnesses; with three demonstrations and one query, every held-out rotation still leaves a witness among the demonstrations.

**Alternative rejected.** The first four-profile repair had only ascending canonical-size examples. Although the global rival was refuted and initial semantic checks passed, a solver could condition “use reading order” on 8×8/9×9. The regression in `checks/tdd-red-canonical-layout.log` exposed this.

**Probe / failure mode.** Task tests enumerate cyclic starts and query rotations for every band. Final census result: 0/1,200 ambiguous rotations.

## D6 — Declare one concrete canonical rival, not a vague uniqueness claim

**Choice.** Implement `reading_order` as the semantic rival and `size_not_reading_order` as its witness. `lesson_identifiable` checks that demonstrations actually refute it.

**Rationale.** Reading order fits all three canonical demonstrations exactly, so it is both plausible and consequential. An executable rival permits repeatable scoring rather than prose-only claims.

**Alternatives rejected.** Identity and geometric transforms do not fit all canonical outputs. Enumerating arbitrary synthesized rules would overstate what finite tooling can certify.

**Probe / failure mode.** The exact 7×7 witness is in `QUESTION_ANSWER.md` and `reference_probe.py`. The final battery verified 60/60 rival claims; the final census found no survivors in production or rotated queries. Other undeclared rivals remain a documented unknown.

## D7 — Use one defensive validator

**Choice.** `self_check` returns diagnostics rather than raising on malformed inputs, accepts all canonical inputs, and enforces only the selected sampler manifold.

**Rationale.** A single authoritative admission boundary avoids the baseline’s contradictory duplicate validators. Defensive handling makes negative tests useful.

**Alternatives rejected.** A permissive “at least two colors” validator admitted zero-object and under-specified cases; duplicating validators makes tool behavior depend on definition order.

**Probe / failure mode.** Tests cover empty, ragged, non-integer, out-of-range, wrong object count, repeated colors, tied areas, and touching/merged cases. Strict-canonical measured 600/600 generated inputs and 3/3 canonical inputs.

## D8 — Retain an independent task-local probe

**Choice.** Add `workspace/reference_probe.py`, with its own component finder, oracle, rival, exact witness, deterministic sampling audit, and optional Racket parity.

**Rationale.** Future reviewers can test the generator without trusting generator internals or reconstructing the semantic argument.

**Alternatives rejected.** Reusing production helpers for every assertion risks correlated bugs. A one-off notebook or prose table would not be replayable.

**Probe / limitations.** On final source, seeds 12000..12199 and sample indices 0..199 in each band produced 600 cases: zero invalid/nondeterministic, 599 unique inputs, all three layout modes, 20 palettes, 45 shapes per band, 399 witnesses, and 4/4 Racket parity. This remains finite sampling.
