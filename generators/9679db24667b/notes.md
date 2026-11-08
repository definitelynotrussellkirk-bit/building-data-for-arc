# Review notes: 9679db24667b

## Baseline diagnosis

The imported `2.0.1` sampler described nine axes but only honored `grid_h` and
`grid_w`, accepted unknown keys, and did not construct its claimed 9-only
distractor row. It generated only qualifying rows, so several reference-lawful
shortcuts fit both the four canonical pairs and every ordinary lesson. The
before battery retained under `checks/before/` failed lint, defect lint, and the
override contract; the semantic stage had no executable contract.

## Repair

Version `3.0.0` keeps the Racket program untouched and narrows the public input
contract to three controls that are fully constructive and observable from
pixels. Unknown keys, non-literal integers (including booleans), and out-of-range
values fail loudly in every band.

A deterministic two-profile schedule alternates canonical-like and teaching
inputs by `sample_index % 2`. Each default canonical slot cycles through one of
the four exact public `(height, width, palette-size)` profiles, restoring
per-band canonical-profile-floor support without narrowing any override domain. The teaching profile simultaneously includes:

- at least two 9s in every qualifying row;
- repeated cells of the single companion color;
- one 9-only row that must stay unchanged;
- one row with two companion colors plus 9s that must stay unchanged.

This kills five named alternatives. With `EXAMPLES_NEEDED = 3`, every ordered
three-example window contains teaching evidence. Every 3-of-4 rotation from a
four-pair window also retains at least one teaching pair.

## Verification design

Task-local tests were written before production changes and initially failed on
12 of 13 tests. The first complete after battery then exposed a per-band exact
canonical-profile floor failure; that run is retained under
`checks/attempts/after-profile-floor-fail/`, and a new failing regression test
was added before the scheduled-anchor repair. The final suite covers all boundary cross-products of the three
axes in all four difficulty settings, canonical parity, deterministic replay,
global-RNG purity, structural impostors, competitor behavior, all cyclic starts,
and query rotations.

`workspace/reference_probe.py` is deliberately independent of generator row
helpers and its Python rule mirror. It reads public pixels, checks all canonical
pairs, iterates the generator's actual competitor declarations, samples every
band, and exhausts two schedule cycles with every query rotation.

## Limits

The generated-counterexample and lesson checks are finite evidence against the
five declared rivals, not a proof of unique induction against every possible
hypothesis. The Python mirror/probe is supplementary; the canonical Racket
program remains label authority. The strict canonical-like half is intentionally
sparse, while the teaching half extends beyond the four published examples to
make the predicate identifiable.
## Current reviewer considerations

Source SHA-256: `037922ecf07311fbc0fc8776bf352c26d0d20e890e6c758074498a82779f94c0`.

# Decisions — 9679db24667b

## D1 — Keep the Racket authority unchanged

**Choice.** Preserve the canonical row-local Racket rule and pin `RULE_HASH = "7ebc4d35864a"`.

**Original rationale.** Unknown; the imported generator had no retained associated notes. The before rule-smoke and authority-sync stages were green, and canonical examples matched the intended rule.

**Alternatives considered.** Rewriting the rule to match the weak sampler was rejected because labels were correct and the defect was in the input/lesson distribution. A Python-only labeler was rejected because Racket is the packet authority.

**Probe / failure mode.** Canonical parity is covered by task tests and the independent oracle. Any later Racket drift is caught by the hash pin, rule smoke, and authority sync.

## D2 — Replace nine misleading axes with three honest exact controls

**Choice.** Expose only `grid_h`, `grid_w`, and `n_positive_rows`, with strict integer domains and rejection of unknown keys.

**Original rationale.** The baseline advertised palette, texture, density, and related controls that did not alter ordinary outputs. The override checker also found declared values rejected differently by band.

**Alternatives considered.** Implementing every old axis would add artificial variation unrelated to the rule and preserve misleading aliases. Keeping singleton axes as diagnostics was rejected because they provided no useful training control. Silently accepting unknown keys was rejected because misspellings become false passes.

**Probe / failure mode.** Tests exhaust every min/max cross-product in `None/easy/medium/hard`, reject booleans/floats/strings/out-of-range/unknown keys, and verify pixel-observable round trips. The remaining risk is that exact controls constrain only dimensions and positive-row count, not every layout detail; that is intentional.

## D3 — Alternate canonical and teaching profiles

**Choice.** Use a deterministic two-slot schedule: even indices are canonical-profile inputs; odd indices are teaching-profile inputs.

**Original rationale.** Canonical support matters for distribution continuity, but canonical examples alone permit several plausible shortcuts. A separate teaching profile can carry decisive negatives without erasing the original task shape.

**Alternatives considered.** Purely random witness insertion was rejected because complete lessons could miss a branch. Teaching-only generation was rejected because it would fail canonical profile support and shift the visual distribution. A longer opaque schedule was rejected as unnecessary.

**Probe / failure mode.** With `EXAMPLES_NEEDED = 3`, any consecutive three examples contain at least one teaching input; any three-of-four rotation in a four-pair window also retains teaching evidence. Exhaustive task tests cover all starts across two cycles, while the 300-lesson census checks the production assembler. This assumes downstream lessons use the declared consecutive schedule; arbitrary external subsampling needs its own gate.

## D4 — Put all decisive branches into each teaching input

**Choice.** Every teaching grid has: multiple `9`s in a qualifying row; repeated cells of its one companion color; one 9-only row; and one row containing two companion colors plus `9`s.

**Original rationale.** These jointly distinguish “replace first 9,” “exactly one companion cell,” “choose first color,” “choose majority color,” and “borrow a nearby row color.”

**Alternatives considered.** Spreading one witness across many inputs was rejected because query rotation could remove the only refuting demonstration. Using contrived colors outside ARC’s 0–9 palette was invalid. Adding more unrelated distractors was rejected as noise.

**Probe / failure mode.** Four executable witness predicates fire in every band; all five competitor functions disagree with the intended output on teaching inputs. The finite set is not exhaustive, so undeclared hypotheses remain a documented limitation.

## D5 — Guarantee exact canonical-profile anchors without weakening overrides

**Choice.** Canonical schedule slots cycle through all four public `(height, width, qualifying-row-count)` anchors. `_scheduled_axis` permutes the complete legal option set so `GenCtx.draw_choice` selects the scheduled default while every explicit override remains available and provenance-backed.

**Original rationale.** The first repaired sampler passed focused semantic/override checks but the full battery found zero exact canonical profile hits in medium and hard mode.

**Alternatives considered.** Hard-coding dimensions outside `GenCtx` was rejected because it would lose exact-axis provenance. Narrowing medium/hard domains to canonical values was rejected because it would make public overrides dishonest. Probabilistic anchors were rejected because the 20-draw profile-floor gate could miss them.

**Probe / failure mode.** The failed full-battery iteration is retained under `checks/attempts/after-profile-floor-fail/`; a regression test was added before the fix. The final profile-floor gate is green in all bands, and every canonical schedule slot maps to a public profile.

## D6 — Use an independent probe, not only self-reported hooks

**Choice.** Add `workspace/reference_probe.py`, which reads pixels directly, supplies its own row oracle/classifier, loads actual competitor declarations, and checks canonical pairs, generated samples, cyclic starts, and rotations.

**Original rationale.** Generator-owned `self_check`, `rule_mirror`, and witness predicates could share a bug. Independent evidence reduces correlated-error risk and gives future reviewers a cheap replay tool.

**Alternatives considered.** Copying the generator helpers or rival-name list into the probe was rejected because that would only duplicate assumptions. Treating the probe as label authority was rejected; Racket remains authoritative.

**Probe / failure mode.** Final report `checks/probes/9679db24667b-independent-probe-final.json` is bound to generator and probe hashes. It samples 100 inputs per band and exhausts the small schedule, but it still cannot prove properties outside the finite public domains or against unnamed rivals.

## D7 — Preserve failures and honest solve exposure

**Choice.** Keep the failed profile-floor battery, the externally interrupted checkpoint run, the successful resume, one-revision blind solve, and one-revision exposed solve.

**Original rationale.** These records distinguish observed defects from post-hoc claims and bind the solve to exact generator bytes.

**Alternatives considered.** Deleting failed evidence to simplify the return was rejected. Inventing a failed solve for contrast was rejected. The exposed solve correctly declares prior rule exposure.

**Probe / failure mode.** `solve/summary.json` carries final generator SHA `037922ec…f94c0`; `solve-blind/summary.json` names its separate task and generator. Hidden labels remain unknown.
