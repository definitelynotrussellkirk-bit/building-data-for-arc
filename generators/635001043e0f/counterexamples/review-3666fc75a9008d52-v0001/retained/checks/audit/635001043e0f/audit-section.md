## 635001043e0f

**Finding A635-1 — Reproduced canonical coverage defect; findings only, generator unchanged.** Version `2.1.0` generates correctly transformed examples in the measured sample, but excludes two behaviors required by the canonical task. The validator accepts only **2/4 canonical inputs**, despite actual Racket execution matching **4/4 canonical labels**. This is a mismatch between canonical coverage and the chosen generator/validator domain, rather than an observed wrong label on an emitted sample.

Source SHA-256: `9128a38e35355adef14158b152703076c210b4e0e405d3e66a65a2b3221288af`.
Executed Racket text SHA-256: `674f34fcacb3e5b62debd252eefd58f22ce0b9f786abdce4c9d0d9a66ad5cc95` (selected rule ID/hash `635001043e0f` / `b5d5d3d1ce89`). No rule or source was modified.

### Concrete canonical witnesses

- **Canonical variant 0, train pair 0:** Input and output are 23 rows × 19 columns. The left-tab object at bounding box `(2,11)..(4,14)` produces a mirror whose far tab falls outside column 18. Racket paints the eight in-bounds copy cells and clips the out-of-bounds cell. `self_check` rejects this input with `mirrored copy would leave the grid`. The explicit rival **skip the whole copy if any part is out of bounds** disagrees with the canonical/Racket result in **8 cells**.
- **Canonical variant 0, test pair 0:** Input and output are 28 rows × 29 columns. The left-tab object at bounding box `(4,2)..(8,8)` contains a **5×6 hollow frame**. `self_check` rejects it as `object is not a canonical hollow rectangle plus one-cell tab`, because `_is_hollow_tabbed_object` tries only frame dimensions 3 through 5. The rival **stamp only frames with both dimensions between 3 and 5** agrees with all **3/3 canonical training pairs**, but disagrees with this query's canonical/Racket output in **19 cells**. This rival does not fit all four labeled canonical pairs and is not claimed to do so.

Both witnesses are existing canonical inputs, not emitted samples or invented validator-admitted cases. They are outside the generator's documented fully-in-bounds/size-restricted domain; the first demonstrates that this domain omits a canonical training behavior. The retained counterexamples include full inputs, actual Racket outputs, both rival outputs, differing coordinates, validator errors, provenance, and source/rule hashes in `checks/audit/635001043e0f/counterexamples.json`.

### Emission and label checks

The deterministic census used **seeds 0–2 × sample indices 0–19 × easy/medium/hard**, no overrides: **180 distinct generated inputs**, **0 generation exceptions**, and **180/180 validator acceptances**. Both deficient rivals agreed with an independent Python transcription of the canonical transform on **180/180** of these inputs. Actual public-CLI Racket checks covered **seed 0, indices 0–11, all three bands**: **36/36** generated outputs matched the independent transform and both rivals, with **0 execution/valid-output failures**. The same Racket batch included all four canonical pairs, making **40/40** valid outputs and expected-label/transform matches overall.

The finite samples support the reported counts. Code inspection separately establishes the support restriction: ordinary generation selects frame dimensions only from 3..5 (easy 3..4), and requires every proposed copy cell to be in bounds. Thus changing random seeds alone cannot supply either missing witness. This is a teaching limitation, not proof of incorrect generated labels. Degenerate textures were not included in this census.

**Recommended correction:** admit and deliberately sample canonical-style partial copies near borders; recognize hollow frames by their geometry instead of the fixed 3..5 template table; include frame widths of at least 6. Retain both canonical witnesses as regression cases and ensure complete generated lessons expose the behaviors they are intended to teach.

### Additional reproduced API issue: A635-2

Advertised `AXES` overrides for `direction` and `n_objects` are ignored by ordinary sampling. At seed 0/sample 0, requesting `direction="up"` produced right, right/down, and right/right/left objects in easy, medium, and hard respectively (**3/3 override violations**). Requesting `n_objects=1` produced 2 objects in medium and 3 in hard (**2/3 violations** across the three bands; easy happened to produce 1). All six override outputs passed `self_check`. The source uses direct random choices for these values instead of consuming their overrides. Honor those knobs, or remove their advertised support. Exact probes are retained in `probe-report.json`.

### Scope and reproduction

`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `LESSON_SCHEDULE_PERIOD` are not declared by this source. No task-local tests or current `review_index.json` were present; the task's associated-notes file was empty. The audit inspected the selected source, its notes and summary, the canonical authority, all four normalized canonical pairs, and the public reviewer helper. No shared source, assignment, generator, rule, or solve record was edited.

Lesson demonstration count and ordering/query policy are unspecified by this generator. **Production lesson verdict: unknown; query-rotation verdict: unknown.** No lesson identifiability claim follows from these individual-grid checks, and this audit does not cover undeclared rivals or all validator-admitted inputs.

Replayable probes: `checks/audit/635001043e0f/probe.py` and `summarize.py`. Exact argument arrays, wrapper working directory (`packet_root`), actual payload working directory (`WORK/repo`), exit codes (all verification commands returned 0), and evidence paths are in `checks/audit/635001043e0f/commands.json`. Detailed counts and all 40 actual output comparisons are in `summary.json`; `input.json`, `cases.json`, and `racket.json` retain the full batch. The two failing canonical/validator cases and rival disagreements are retained rather than discarded. The final generator hash was rechecked against the source-bound Racket report.
