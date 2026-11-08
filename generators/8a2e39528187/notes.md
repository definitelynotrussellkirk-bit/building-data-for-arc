# Working notes: 8a2e39528187

## Review finding

The imported `2.0.0` sampler and validator modeled a narrower rule than the selected authority:

- It merged all touching nonzero cells, even when colors differed. One canonical input therefore appeared to contain three objects and was rejected, although the Racket `objects` operation treats monochromatic 4-connected regions as separate objects.
- It required strictly distinct areas and never generated the canonical equal-area branch. The authority resolves ties by lexicographic bounding box after area.
- Its prose suggested an ascending consecutive palette such as `2,3,4,5`; the actual rank palette is fixed at `2,4,6,8`.
- Several advertised controls were not observably honored, failed blob placement was accepted silently, and difficulty labels did not change the sampled distribution.

The canonical rule itself remained internally consistent with all five official pairs, so no authority edit was justified.

## Selected repair

Version `3.0.0` keeps exactly four monochromatic objects and the canonical grid envelope. A deterministic four-slot schedule teaches:

1. `canonical_strict`: distinct areas with input colors detached from rank;
2. `tie_break`: equal area `2,2,4,5`, where bounding-box order matters;
3. `touching_colors`: unlike-colored objects share a 4-neighbor boundary but remain separate;
4. `rank_palette`: input colors are the same set as the output palette but deliberately deranged.

The schedule is indexed by `sample_index mod 4`, so every four-demo window covers all profiles. A keyed RNG includes the difficulty band; bands remain semantically equivalent but are not byte-identical. Exact `grid_h`, `grid_w`, and `lesson_profile` overrides are validated and recoverable with `observe_overrides`.

## Rival and witness contract

Retained witnesses target actual plausible shortcuts:

- cross-color contact versus color-blind connected components;
- equal-area tie versus reversed bounding-box tie order;
- deranged rank palette versus numeric input-color order;
- area/position conflict versus scan order;
- ascending area versus descending area.

`lesson_identifiable` requires every declared rival to disagree with at least one visible demonstration. This is finite rival coverage, not universal proof of human or model induction.

## Verification scope

`tests/test_generator.py` covers canonical acceptance/output parity, rule hash, exact overrides, schedule coverage, witnesses/rivals, determinism, diversity, invalid controls, and distinct difficulty streams. `tests/test_lesson_probe.py` covers the independent oracle and census logic.

`workspace/lesson_probe.py` is source-bound and records generator/probe hashes, actual sampler formulas, domain limits, canonical rival fit, unique inputs, profile counts, cyclic residues, and rival survival/query disagreement. The final census used 100 lessons per band (300 total, 1,500 generated rows) and required the real selected Racket program; it found zero validation errors, zero unidentifiable lessons, zero surviving rivals, and zero Racket mismatches.

## Remaining limitations

The curriculum intentionally covers only four objects, dimensions 9–10 by 10–12, and size profiles `2,3,4,5` or `2,2,4,5`. It does not claim the selected rule is defined for arbitrary object counts or that finite rival elimination guarantees Qwen3.5-9B will infer the rule. The shape library is compact and favors small polyominoes so semantic branches can be guaranteed without placement retries.

Imported associated notes retain their original evidence and timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `2e72914c263a0db7850e69e612c5f1361b127bb9663ab1ca75a3ac39315f5556`.

# Design decisions — 8a2e39528187

The imported source had no retained design rationale beyond its docstring and summary. Where the original intent is not explicit, the rationale below is marked as inferred rather than asserted.

## D1 — Preserve the selected rule authority

**Choice.** Keep the canonical Racket program unchanged and pin its normalized hash as `76fcc8e7f591`.

**Why.** The selected program solves all four train pairs and the test pair, and the independent Python oracle agrees with it. The observed failures came from the generator and validator, not the authority. Final rule-smoke and authority-sync execute the selected sources successfully.

**Rejected alternative.** Editing the rule to require non-touching objects or strictly distinct areas would make the authority conform to the imported sampler but contradict official inputs. That would be source drift, not a repair.

**Probe / limitation.** `checks/after/checks/8a2e39528187_after_authority_sync.json` verifies selected-source synchronization and execution parity. One archival raw source is textually different but behaviorally canonical; it was left untouched.

## D2 — Use monochromatic 4-connected objects

**Choice.** Treat each same-colored 4-connected nonzero region as an object. Four distinct colors are required, but unlike-colored objects may share an edge.

**Original rationale.** The old color-blind component scan was likely a convenience inherited from a “separated blobs” generator; no explicit rationale was retained.

**Why.** Canonical train[2] contains unlike-colored edge contact, and the selected `objects` primitive separates by color. This is finding G1.

**Rejected alternatives.** Requiring a background gap deletes a real authority branch. Treating all nonzero contact as one object rejects a canonical input and supports a color-blind shortcut.

**Probe / failure mode.** The `touching_colors` profile guarantees a contact witness, while `color_blind_components` is an executable rival. A future shape-library change could accidentally eliminate contact, so both the witness test and the lesson census are retained.

## D3 — Keep four objects and canonical-size canvases

**Choice.** Generate exactly four objects on 9–10 by 10–12 grids.

**Why.** Every official input has four objects and lies in this envelope. Keeping the task-local domain tight makes semantic branches guaranteed and avoids teaching unsupported object-count behavior.

**Rejected alternatives.** The old wider prose envelope and arbitrary blob counts were not exercised by the authority examples. Expanding them would add quantity without evidence that rank colors beyond four or truncated palettes are intended.

**Probe / limitation.** Profile floor reports 50/60 exact canonical-size/palette profiles and 60/60 envelope hits. This deliberately does not claim validity for other object counts or arbitrary dimensions.

## D4 — Cover both strict and tied area profiles

**Choice.** Use area profiles `(2,3,4,5)` and `(2,2,4,5)`. Equal-area objects are ordered by lexicographic bounding box.

**Original rationale.** The old generator explicitly forced distinct sizes, apparently to make ranking easy; it did not document why the official tie was omitted.

**Why.** The authority sorts by `(obj-size, obj-bbox)`, and one official pair contains the tie. A strict-only sampler leaves the reverse-tie rival indistinguishable on 4/5 official pairs.

**Rejected alternatives.** Randomly allowing ties without a guaranteed lesson branch is underpowered. Larger or multiple ties add complexity without canonical evidence.

**Probe / failure mode.** `tie_break` guarantees a two-object tie and `reverse_bbox_ties` must disagree. Placement changes could accidentally make the rival agree, so exact rival disagreement is tested rather than inferred from the profile name.

## D5 — Separate input colors from output rank colors

**Choice.** Output rank colors are fixed to `2,4,6,8`. Most inputs use distinct distractor colors; the `rank_palette` profile uses the same set but in a derangement relative to rank.

**Original rationale.** The imported summary mentioned examples such as `2,3,4,5`, which was simply inconsistent with the selected rule.

**Why.** The derangement demonstrates that input color identity and numeric color order are irrelevant. It also prevents identity-copy solutions when input colors happen to equal the output palette set.

**Rejected alternatives.** Always excluding rank colors makes the transformation visible but never tests the strongest palette shortcut. Always using the rank palette makes the distribution unnecessarily narrow.

**Probe / failure mode.** `numeric_input_color_order` is the executable rival. The profile observer recovers `rank_palette` only from actual pixels, so an advertised profile cannot pass merely through metadata.

## D6 — Use compact dihedral polyominoes with constructive placement

**Choice.** Draw sizes 2–5 from a small set of connected base shapes and their dihedral transforms, then place them constructively under profile-specific constraints.

**Why.** Compact shapes fit every canonical canvas and let contact, scan-order conflict, and tie order be guaranteed without accepting failed placement. Shape transforms retain useful geometry variation.

**Rejected alternatives.** The old random neighbor-growth loop could exhaust retries and silently return fewer/lower-quality objects. A much larger free-form shape grammar would make branch guarantees fragile for little additional semantic value.

**Probe / limitation.** Diversity is 100% over the official 300-pair sample, but the shape family remains compact. This is a curriculum distribution, not a model of all possible polyominoes.

## D7 — Use a deterministic four-slot lesson schedule

**Choice.** `sample_index mod 4` selects `canonical_strict`, `tie_break`, `touching_colors`, and `rank_palette`. `EXAMPLES_NEEDED = 4`, so every consecutive four-example window covers all profiles.

**Why.** Random branch selection can have good marginal frequencies while individual lessons omit the one counterexample needed to eliminate a shortcut. A cyclic schedule gives a lesson-level guarantee at negligible cost.

**Rejected alternatives.** Independent random profiles and frequency-only semantic gates were rejected because they do not prove complete lesson support. Hard-coding one fixed four-grid lesson would destroy diversity.

**Probe / failure mode.** Tests exhaust 12 cyclic starts. The 100-lessons-per-band probe uses stride 11, visits every start residue, and records no surviving competitor. The schedule covers the declared rivals only; it is not universal induction evidence.

## D8 — Advertise only exact, observable controls

**Choice.** `AXES` contains `grid_h`, `grid_w`, and `lesson_profile`. All are validated, exact, and recoverable from the generated grid. Unknown controls fail loudly. Helpful/degenerate texture lists are empty.

**Original rationale.** The old module appeared to inherit a generic axis template. Several controls were singleton, ignored, or aliases with overlapping domains.

**Why.** Training tooling should not believe it is sweeping an axis that never changes pixels. A smaller truthful contract is better than a large decorative one.

**Rejected alternatives.** Keeping `palette_size`, `density`, `position_bias`, or `texture` as diagnostic names would preserve compatibility but still encourage false coverage claims. They were removed instead.

**Probe / failure mode.** The final override gate covers 36 cases across 3 bands and accepts 3,240/3,240 draws. Task tests also check invalid dimensions, profiles, and unknown keys.

## D9 — Make difficulty streams distinct without changing semantics

**Choice.** Difficulty is included in keyed layout draws so easy, medium, and hard are deterministic but not byte-identical. The same semantic schedule and legal domain apply to every band.

**Why.** The intermediate repair triggered the dead-band detector because difficulty never entered any draw. Distinct streams improve sample diversity and make per-band audits meaningful.

**Rejected alternative.** Inventing unsupported semantic “hardness” tiers—more objects, more colors, or larger ties—would exceed the authority domain. The final bands differ in layout stream, not in claimed conceptual complexity.

**Probe / limitation.** A regression test requires the three default sequences to differ. These labels should not be interpreted as calibrated human/model difficulty.

## D10 — Declare executable rivals and require lesson-level elimination

**Choice.** Retain five competitors: color-blind components, reverse bbox ties, scan order, numeric input-color order, and descending area. `lesson_identifiable` requires each to fail on at least one visible demonstration.

**Why.** These are concrete shortcuts suggested by the official pairs and old sampler. Two of them fit 4/5 canonical pairs, so they are especially important for generated data.

**Rejected alternatives.** A prose-only rival list cannot be tested. Calling the rule “uniquely identifiable” against all possible programs would be unsupported.

**Probe / limitation.** The final census iterates the generator's actual `LESSON_COMPETITORS`, records canonical fit and every lesson's rival survival, and found zero survivors in 300 lessons. Unknown rivals may still exist.

## D11 — Retain independent tests and a real-Racket census

**Choice.** Add task-local regression tests plus `workspace/lesson_probe.py`, whose output oracle is implemented independently of the generator mirror and whose `--racket` mode fails rather than falling back.

**Why.** Official smoke gates are necessary but use small samples. The assignment specifically called for at least 100 lessons per band when plausible rivals fit canonical pairs.

**Rejected alternatives.** Reusing `rule_mirror` inside the census would only prove self-consistency. Reporting witness frequencies without assembling complete lessons would not test teaching value.

**Probe / limitation.** Final source hash `2e72914c…` was checked on 1,500 unique rows with 1,500/1,500 Racket agreement. The census is reproducible for this finite sampler and rival set only.
