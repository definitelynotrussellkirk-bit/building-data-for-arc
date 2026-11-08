# Working notes: 302ddfbe2baa

## Review `review-368602194429b92c`

Baseline generator SHA-256: `6d66be0a40b89044a59491cdaea79f07718f631e6952fca9e57d862df3808c4c`.
Final generator SHA-256: `2624691778323d7fd756ad82817a5802d5cac2b9101236cd61c67d4a4e3f3439`.
Canonical rule hash: `923c6879d312` (authority unchanged).

### Baseline findings

- `RULE_HASH` was missing.
- Helpful textures `default`, `sparse`, `dense`, and `all_blocked` were dead overrides.
- Degenerate controls overlapped the ordinary texture domain.
- `self_check` rejected only 19/63 destructive mutations and accepted singleton, line, 2×2, and full-one-color impostors.
- The input grammar did not expose four canonical-fitting shortcuts: stop at any nonzero, use rightmost maroon, head toward nearest maroon, or process only the first three emitters.

The initial before battery was interrupted after four stages and remains intentionally incomplete. It had 2 green, 2 failed, and 8 pending stages; lint and defect lint were the decisive failures.

### Repair

Version 2.0.0 uses a deterministic three-slot curriculum:

1. `canonical` — strict anchor;
2. `pass_through_distractor` — color 2 inside a live ray, plus 4–5 emitters;
3. `multi_blocker` — nearer left maroon plus first and second right maroons.

Every three consecutive examples contain all profiles. Exact public controls are limited to pixel-observable `grid_h`, `grid_w`, `emitter_count`, and `scene_kind`. The validator enforces dimensions, palette, one emitter per active row, at least one maroon per input, live rightward zeros, and profile-specific witness structure.

Named rivals and witnesses are executable and registered through `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, `strict_canonical_like`, and `lesson_identifiable`.

### Verification

- Full after battery: 12/12 green.
- Portable task tests: 57/57 passed.
- Lesson census: 100/100 materialized per band; 0 ambiguous, hook warnings, or scoring errors.
- Independent cyclic probe: 600 three-example windows, 0 contract failures.
- Visible post-repair solve: 3/3 demonstrations passed on first general program; earlier exposure declared yes.

### Retained tool

`workspace/reference_probe.py` is a public-data-only independent oracle and cyclic schedule checker. It iterates the generator's actual rival registries rather than copying names. Run from `repo/`:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/302ddfbe2baa/workspace/reference_probe.py \
  --starts 100 --out ../checks/reference-probe-verification.json
```

### Limitations

The contract eliminates four concrete canonical-fitting rivals, not all conceivable hypotheses. The generated grammar intentionally keeps one emitter per active row and a small fixed semantic palette; future expansion should add a named rival and witness before adding visual variation for its own sake.
## Current reviewer considerations

Source SHA-256: `2624691778323d7fd756ad82817a5802d5cac2b9101236cd61c67d4a4e3f3439`.

# Decisions for `302ddfbe2baa`

## D1 — Preserve the canonical Racket authority

**Choice.** Leave `repo/shared/data/canonical/puzzles.jsonl` and the bank authority unchanged; pin `RULE_HASH = "923c6879d312"` in the generator.

**Original rationale.** Unknown. The baseline omitted a rule hash, but the rule smoke already produced correct outputs and no discrepancy in the authority was found.

**Alternatives considered.** Rewrite the Racket rule for explicit distractor handling; add a second rule variant. Both were rejected because the existing authority already preserves nonzero cells, paints only zeros, and stops only at maroon 9.

**Probe.** Before rule smoke passed; final rule smoke and authority sync passed on the same authority-set hash. `checks/question/racket.json` also verifies a distractor witness directly.

**Failure modes and limits.** A pinned hash prevents silent rule drift but does not by itself prove the Python semantic mirror is correct. Canonical-pair parity and direct Racket applications cover that boundary.

## D2 — Replace probabilistic teaching with a three-slot curriculum

**Choice.** Cycle `canonical → pass_through_distractor → multi_blocker` by `sample_index % 3`.

**Original rationale.** The baseline used independent random placement. Its original rationale is unknown; empirically, it produced no guaranteed lesson-level distinction between canonical-fitting shortcuts.

**Alternatives considered.** Pure random mixtures; a six- or nine-slot curriculum; one overloaded example containing every witness. Pure randomness leaves nonzero probability of ambiguous lessons. Longer schedules are unnecessary for four rivals. An overloaded scene is harder to parse and makes counterfactual attribution weaker.

**Probe.** The independent reference probe checks all cyclic starts, not only aligned blocks. Across 600 windows, every named competitor was refuted and every profile appeared in every window.

**Failure modes and limits.** This guarantee depends on three-example lesson assembly. A future consumer that samples arbitrary nonconsecutive examples must use `lesson_identifiable` or an equivalent assembly check.

## D3 — Keep a canonical anchor in every lesson

**Choice.** Reserve one of three slots for a strict canonical-like example.

**Original rationale.** The public task has a small, clean visual grammar. Removing anchors entirely could teach only edge cases.

**Alternatives considered.** All three examples as adversarial probes; 50% or greater canonical sampling. All-probe lessons risk distribution drift. Majority-canonical lessons reduce witness density and can leave a three-example lesson without both required probe classes.

**Probe.** The final semantic gate measured 207/600 strict examples (34.5%), and profile-floor found 37/60 exact canonical profiles. Both exceed the 0.20 strict minimum while preserving two witness slots.

**Failure modes and limits.** The exact canonical-size/palette profile is still only a subset of all generated anchors. The strict hook defines and tests the accepted envelope explicitly.

## D4 — Declare only pixel-observable exact axes

**Choice.** Expose four exact axes: `grid_h`, `grid_w`, `emitter_count`, and `scene_kind`.

**Original rationale.** The baseline advertised palette, texture, density, position, and color-count controls whose effects were dead, redundant, or unobservable. Four helpful textures were byte-identical to default draws.

**Alternatives considered.** Preserve compatibility aliases; make every old texture real; mark old axes diagnostic. Compatibility aliases would keep misleading API surface. Realizing all old textures adds variation that does not serve the rule. Diagnostic declarations are inappropriate for values users expect to control exactly.

**Probe.** `observe_overrides` recovers each value from pixels. The override battery exercised 141 cases and 12,690 accepted draws, including joint controls and boundaries.

**Failure modes and limits.** Removing old axis names is an interface break for callers that relied on undocumented behavior. Because those controls were already silently ignored, failing loudly is safer than preserving false semantics.

## D5 — Require a maroon anchor in every accepted teaching input

**Choice.** Every accepted input contains at least one maroon blocker, including one-emitter cases.

**Original rationale.** The first repaired draft allowed a lone unblocked emitter; defect lint showed this was a shape-blind singleton impostor under the task grammar.

**Alternatives considered.** Allow all-edge rays as lawful singleton scenes; classify them as a degenerate texture. Rejected because an all-edge singleton does not expose blocker identity and is unnecessary for the curriculum.

**Probe.** A regression test was written first and failed on the permissive draft; after the grammar boundary changed, the task-local suite and strict defect linter passed.

**Failure modes and limits.** Edge-reaching rays still occur on other rows, so boundary behavior remains represented. The restriction applies to whole inputs, not every emitter row.

## D6 — Name four rivals and pair each with an executable witness

**Choice.** Declare `stop_at_any_nonzero`, `rightmost_maroon`, `toward_nearest_maroon`, and `first_three_emitters` in `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`.

**Original rationale.** All four match all three usable canonical pairs. They correspond to independent ambiguities: blocker color, blocker ordering, direction, and object count.

**Alternatives considered.** Add many syntactic variants of the same rule; omit the emitter-count rival. Syntactic duplicates inflate counts without expanding semantic coverage. The emitter-count rival is retained because every canonical example has exactly three emitters.

**Probe.** The independent tool first verifies 3/3 canonical fits, then tests each cyclic generated lesson. The shared census independently scores the registry declarations.

**Failure modes and limits.** The list is finite. It is evidence for these ambiguities, not a proof that no other rival exists.

## D7 — Build an independent portable reference probe

**Choice.** Add `workspace/reference_probe.py`, using its own Python oracle and iterating the generator's actual rival registries.

**Original rationale.** The shared census is source-bound and broad, but it does not rotate every pair into query position. Future agents also need a fast, task-local way to detect schedule regressions without reading private runner internals.

**Alternatives considered.** Rely only on unit tests; copy rival names into a one-off script; invoke private Racket runner functions. Unit tests alone would not retain a census artifact. Copying names risks registry drift. Private runner imports violate the packet's evidence guidance.

**Probe.** The script reports generator/rule hashes, verifies each shortcut fits every canonical pair, and checks 100 cyclic starts × two seeds × three bands. `checks/reference-probe-final.json` is green.

**Failure modes and limits.** It mirrors the public Racket semantics in Python; direct supported `arcpuzzles apply` receipts are retained for the highest-value disagreement witness.

## D8 — Preserve interrupted evidence rather than rewriting history

**Choice.** Keep the incomplete before battery and the separately interrupted first after run, then perform a clean authoritative rerun.

**Original rationale.** The packet explicitly says running/interrupted aggregates are not passes and should be retained separately.

**Alternatives considered.** Delete partial outputs; merge child receipts manually into a pass. Both would obscure execution history or overstate the wrapper's aggregate state.

**Probe.** `checks/before/` remains incomplete; `checks/after-interrupted/` remains incomplete; `checks/after/` is the distinct all-green rerun.

**Failure modes and limits.** The first after interruption exposed a shared wrapper/checkpoint usability issue documented as F1; it was not a repaired-source failure.
