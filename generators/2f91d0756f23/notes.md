# Working notes: 2f91d0756f23

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `dd8d326a182b8565811e8a476bcdcfdf453cac3f049b384ce754c843f271e823`.

# Decisions — `2f91d0756f23`

Final generator SHA-256: `dd8d326a182b8565811e8a476bcdcfdf453cac3f049b384ce754c843f271e823`.

## D1 — Preserve the Racket authority

**Choice.** Keep the canonical Racket row byte-identical and pin `RULE_HASH = "dc9e50b0f1e3"` in Python.

**Rationale.** Before-repair `rule_smoke`, Racket lint, grammar, and authority sync were green. The defects were generator binding, controls, distribution, and teaching semantics—not the oracle.

**Alternative rejected.** Rewriting the Racket program would expand the trusted change surface without addressing any reproduced failure.

**Probe.** Full before/after batteries and canonical mirror tests. The authority-set hash remains `3c8b607fc188779dd72c3cdedf3862794e19df1feabf93393fb262992c3002cb` in both aggregate reports.

**Failure mode/limitation.** The Python mirror is secondary test code; Racket remains authoritative.

## D2 — Make every advertised axis exact, typed, and observable

**Choice.** Retain the four public axes (`grid_h`, `grid_w`, `k`, `n_orbits`), validate types/ranges up front, reject unknown names, route all values through keyed `GenCtx` draws, and expose them through `observe_overrides()`.

**Rationale.** The baseline declared these controls but ignored them, producing `38,423` findings. A declared axis that cannot be requested exactly makes targeted dataset balancing and diagnosis unreliable.

**Alternative rejected.** Removing the axes would hide the defect and make curriculum construction less controllable. Silently clipping or coercing invalid values was rejected because it turns typos into mislabeled experiments.

**Probe.** Override stage covers `372` cases across three bands and `33,480` draws; final findings and warnings are both zero. Task tests include boundaries, combinations, invalid values, unknown keys, and observability.

**Failure mode/limitation.** The legal ranges remain the original advertised ranges; this repair does not claim shapes outside them are semantically invalid.

## D3 — Use a four-slot schedule rather than independent random `k`

**Choice.** Set default `k` by `sample_index mod 4` to `1,2,3,4`, with `EXAMPLES_NEEDED = 4`.

**Rationale.** A four-demo ARC lesson needs evidence for all count values. Independent sampling can omit values and leave `always_four_turns` or other count shortcuts alive even when the global corpus is diverse.

**Alternative rejected.** Pure i.i.d. sampling was cheaper but provided only marginal witness frequency, not complete-lesson identifiability. Rejection sampling per lesson would require state outside the per-sample generator.

**Probe.** Task test checks every cyclic start. Deep probe covers each start residue exactly 25 times per band and finds `0/300` unidentifiable lessons.

**Failure mode/limitation.** `k` is correlated with schedule slot in default lessons. Callers using exact overrides can break the default teaching schedule and must assemble lessons deliberately.

## D4 — Reserve two slots for canonical profiles and two for generalization

**Choice.** Emit 8×8/`k=1` and 9×9/`k=3` canonical-profile slots; retain band-shaped broad dimensions in `k=2` and `k=4` slots.

**Rationale.** The baseline had zero support for the canonical 8×8/9×9, five-color profiles. Using only canonical shapes would overfit; using only broad random shapes failed the profile floor.

**Alternative rejected.** A weak probabilistic prior could still produce zero hits in a small band sample. Making all samples canonical-sized would erase useful size generalization.

**Probe.** Final profile floor reports `31/60` exact hits with support in each band. Deep probe sees `750/1,500` canonical-profile hits while also observing broad legal dimensions.

**Failure mode/limitation.** Canonical-profile matching uses coarse `(height,width,palette-size)` support, not a claim that every canonical morphology is reproduced.

## D5 — Teach marker counting with non-prefix headers

**Choice.** Keep the public left-prefix form in one canonical slot, but sample marker columns from `1..w-1` in the other three slots.

**Rationale.** `left_prefix_count` fits all three usable canonical pairs. Non-prefix placements force counting all color-1 cells rather than scanning a prefix.

**Alternative rejected.** Always using non-prefix headers would abandon the public texture; always using prefixes would preserve the shortcut.

**Probe.** `nonprefix_header` fires `437/600` semantic census draws; all `60/60` checked witness cases disagree with the rival. The deep probe records 375 disagreements per band over 500 inputs.

**Failure mode/limitation.** Marker location is still restricted to row zero, matching the authority and declared task.

## D6 — Teach orbit cardinality beyond the canonical two-object shortcut

**Choice.** Use one orbit in the sparse slot, two in canonical slots, and 3/4/5 in the dense easy/medium/hard slot.

**Rationale.** `first_two_orbits_only` also fits every canonical pair. At least one complete lesson example must contain more than two seeds to refute it.

**Alternative rejected.** Random 1–5 draws could miss the required witness in a specific lesson. Always-dense scenes would make early examples unnecessarily difficult and reduce texture diversity.

**Probe.** `more_than_two_orbits` fires `145/600`; all `60/60` checked witness cases refute the rival. Every deep-probe four-demo window contains the dense slot.

**Failure mode/limitation.** The generator keeps the advertised maximum of five despite six geometric rotation classes being available within radius two.

## D7 — Prevent color collisions by construction

**Choice.** Select at most one seed from each quarter-turn equivalence class and give all seeds distinct colors.

**Rationale.** Multiple differently colored seeds in the same orbit can overwrite the same output cells, making labels depend on iteration order rather than the task rule.

**Alternative rejected.** Detecting collisions after placement and retrying is less transparent and harder to validate. Allowing same-color collisions would complicate observability and lesson interpretation.

**Probe.** Dedicated regression test checks input classes and output color counts over many seeds/bands/`k` values; full self-check enforces the invariant.

**Failure mode/limitation.** This intentionally narrows the constructive manifold to unambiguous multi-object scenes, while exact axis ranges remain intact.

## D8 — Use a two-cell anchor margin

**Choice.** Place the color-9 anchor at least two cells from every edge.

**Rationale.** All generated offsets have Chebyshev radius at most two, so every quarter-turn remains in bounds. This removes clipped-orbit ambiguity and makes each input seed's complete intended orbit visible.

**Alternative rejected.** Edge clipping is technically handled by the authority but would create a separate semantic branch requiring dedicated witnesses and could confound count inference.

**Probe.** `self_check()` enforces the margin; strict semantic census accepts `600/600` generated inputs.

**Failure mode/limitation.** The generator does not teach clipped rotations. That is a deliberate documented domain restriction.

## D9 — Declare executable rivals and lesson identifiability

**Choice.** Add four rivals—left-prefix count, first-two-orbits only, opposite rotation, and always-four-turns—plus witnesses, canonical-shortcut declarations, and a complete-lesson hook.

**Rationale.** Static prose about counter-hypotheses is not machine-checkable. Training quality depends on whether complete lessons actually eliminate plausible wrong programs.

**Alternative rejected.** Per-input witness frequency alone can pass while every assembled lesson remains ambiguous.

**Probe.** Semantic gate verifies four witness claims, each `60/60`; smoke lessons are `12/12` identifiable. Deep probe finds no competitor surviving all demos in any of `300` lessons.

**Failure mode/limitation.** Rival coverage is finite and reviewer-authored. It is evidence against named shortcuts, not proof that no other program fits.

## D10 — Build a source-bound deep probe

**Choice.** Add `workspace/review_probe.py`, sampling 100 independent lessons per band, five unique samples per lesson (four demos plus query), all cyclic starts, and the generator's live rival declarations.

**Rationale.** The built-in 12-lesson semantic check is a smoke test. Duties explicitly require at least 100 lessons per band when plausible canonical-fitting rivals exist.

**Alternative rejected.** Copying rival names into a one-off notebook would drift from source declarations. Running 1,500 separate Racket calls would be unnecessarily expensive after rule smoke/authority equivalence had passed.

**Probe.** `checks/deep-probe/2f91d0756f23_deep_probe.json`: 1,500/1,500 unique inputs, zero strict failures, zero unidentifiable lessons, exact per-band axis limits and schedule counts.

**Failure mode/limitation.** Labels in this deep probe use the pinned Python mirror; independent Racket checks are supplied by canonical tests, rule smoke, and authority sync. The report says this explicitly.

## D11 — Freeze source before the exposed solve

**Choice.** Prepare and finish the post-repair solve only after the generator hash was final, then make no generator changes.

**Rationale.** A solve bound to earlier bytes is not evidence about the returned source.

**Probe.** `solve/summary.json` and `checks/fresh-handoff-summary.json` both record `dd8d326a…e823`.

**Failure mode/limitation.** The solve is exposed, not blind; earlier rule exposure is honestly recorded as `yes`.
