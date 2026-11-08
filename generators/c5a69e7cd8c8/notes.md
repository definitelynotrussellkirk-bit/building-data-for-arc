# Working notes: c5a69e7cd8c8

## Current rule and authority

The intended rule is unchanged from the canonical Racket program. A nonzero
color occurring exactly once has one open cardinal neighbour. The output paints
that singleton color through every zero cell on the **opposite** ray while
preserving occupied support cells. `RULE_HASH = bf2554f59664`; final generator
SHA-256 is `132987cd4a2c9f6e2634c8edc5e54db1ff5a493c9a7b3ba6d8c3246150f4b6a0`.

The selected archival `racket_target.target_code` was synchronized byte-for-byte
with the canonical program after the authority gate found only a formatting
difference. Its `raw_code` remains byte-identical to the packet baseline, and
Racket execution parity passed. This was an authority-text synchronization, not
a semantic rule change.

## Reproduced baseline defects

The baseline exposed an unpinned rule, a nonliteral/fake axis contract, ordinary
negative textures, no semantic lesson contract, weak structural validation, and
zero exact canonical-profile support in the easy and hard 20-draw checks. Several
advertised controls were ignored or not recoverable from pixels. Its rigid
triangle/palette construction also supported two canonical-compatible shortcuts:
“transform only the exact canonical triangle” and “infer ray direction from the
singleton palette.” The interrupted baseline aggregate remains `status=running`;
its completed stage failures are retained under `WORK/checks/before/`.

## Selected distribution

Version 2.1.0 constructs lawful scenes from seven exact, observable axes:

- seven canvas profiles, including all four canonical dimensions;
- all four opening directions;
- support depth 2 or 3;
- eight support/singleton palettes, including and decoupling the four canonical
  palettes;
- three longitudinal anchors and three lateral positions;
- zero through five support decorations.

An eight-slot deterministic schedule covers these choices. A training episode
uses three demonstrations plus one query. Every cyclic four-pair window, with
each pair held out in turn, refutes the six declared competitors. Decorations
preserve the monochrome support law while making “exact canonical triangle only”
fail. Palette/direction mismatches make canonical palette lookup fail.

## Reversed decisions during review

1. **Support depth 4 was removed.** It was initially added as broader geometry,
   but the exact override census found that `10x15`, a horizontal opening, and
   depth 4 collapse two advertised lateral labels onto one coordinate. That made
   255 draws undecodable. The truthful supported domain is depth 2..3; after the
   change all 43,650 advertised override draws passed with no incompatibility
   exceptions.
2. **Witness metadata was made executable.** The first strict semantic run found
   zero ambiguous rotations but rejected the contract because witnesses did not
   name the rivals they refuted. `WITNESS_RIVALS` now links every witness to its
   concrete competitor, and the strict gate passes.
3. **Authority text was synchronized, not rewritten.** Canonical and selected
   active rule text differed only by whitespace/minification. Only active
   `target_code` was aligned; archival `raw_code` and rule semantics were kept.

## Evidence and known limits

- Final battery: all 12 stages green in `WORK/checks/after-final/`.
- Exact override matrix: 43,650/43,650 accepted, zero findings, in
  `WORK/checks/override-final-green/`.
- Focused portable tests: 10/10 in `WORK/checks/task-tests-final/`.
- Racket-labelled lesson census: 300 lessons, 1,200 pairs, 1,200 query rotations,
  946 unique inputs, zero ambiguity/errors in
  `WORK/checks/lesson-census-final.json`.
- Source-bound exhaustive schedule probe: 120 windows, 480 rotations, 168
  geometry cases, zero failures in `WORK/checks/curriculum-probe-final.json`.
- Exact rival witnesses are retained in `counterexamples/` and exercised by the
  focused semantic tests.

The contract checks a finite declared rival family, not every possible learned
hypothesis. The reusable curriculum probe labels generated examples with the
independent Python mirror; the larger census and battery provide the Racket-backed
checks. Finite seeds and schedule enumeration do not prove universal induction.
## Current reviewer considerations

Source SHA-256: `132987cd4a2c9f6e2634c8edc5e54db1ff5a493c9a7b3ba6d8c3246150f4b6a0`.

# Decisions for c5a69e7cd8c8

## D1 — Preserve the canonical rule

**Prior choice:** the baseline delegated output to the selected Racket authority,
but did not pin its hash. The rationale for leaving the pin absent is unknown.

**Decision:** keep rule semantics unchanged and pin normalized canonical hash
`bf2554f59664`. The Python implementation remains a review mirror, not authority.

**Alternatives rejected:** rewrite the Racket rule around the generated motif, or
quietly treat the baseline's palette/direction correlations as semantics. Both
would change the task rather than repair its data.

**Evidence / failure mode:** all four canonical pairs pass the mirror and the
Racket rule-smoke stage. The final authority gate passes. The mirror could still
contain a shared misunderstanding, so Racket-backed battery and census evidence
remain primary.

## D2 — Replace inherited generic controls with seven observable controls

**Prior choice:** the baseline advertised generic dimensions, palette, texture,
density and related controls, including negative textures, while several values
were ignored or not recoverable. Its original rationale is unknown.

**Decision:** expose only canvas, opening, support depth, support/singleton
palette, longitudinal anchor, lateral position, and number of support extras.
Every axis changes returned pixels and is decoded by `observe_overrides`; unknown
keys and invalid values fail closed.

**Alternatives rejected:** retain aliases for compatibility, declare hidden
metadata-only axes, or list impossible combinations after the fact. A smaller
truthful contract is more valuable than a broad false one.

**Evidence / limits:** 43,650/43,650 exact draws pass across all three bands and
485 cases. These axes intentionally do not expose every random detail; only
stable caller-facing controls belong in the contract.

## D3 — Use a constructive lawful grammar instead of negative textures

**Prior choice:** the ordinary texture domain included `full_grid`,
`no_singleton`, and `no_support`, overlapping explicit invalid fixtures.

**Decision:** always construct exactly one singleton color, one monochrome
support color, one open cardinal side, a depth-2..3 core, and at least one zero
cell beyond the support on the opposite ray. Decorations are support-colored and
bounded to five cells.

**Alternatives rejected:** generate arbitrary noise and filter, or keep invalid
ordinary examples as “hard” cases. Invalid inputs teach rejection artifacts, not
the ARC transformation.

**Evidence / limits:** self-check, mutation tests and defect lint pass. The
constructive grammar is conservative; it does not claim to enumerate every
mathematically lawful scene.

## D4 — Generalize support shape and decouple palette from direction

**Prior choice:** the baseline emitted a rigid canonical triangular motif and
coupled the four canonical palettes to directional cases. That permitted exact
triangle and palette-direction shortcuts.

**Decision:** retain canonical dimensions/palettes for support while add four
new palettes, support decorations, all four directions and several placements.
Schedule these so every supported lesson window contains witnesses against the
two canonical-compatible shortcuts.

**Alternatives rejected:** only increase random canvas size, or only add more
canonical triangles. Neither changes the shortcut-supporting causal structure.

**Evidence / limits:** both retained counterexamples have Racket outputs and
focused rival checks. Canonical shortcuts fit all official pairs and are refuted
by generated witnesses. Other undeclared visual shortcuts remain possible.

## D5 — Three demonstrations, four-pair cyclic windows, all query rotations

**Prior choice:** baseline lesson semantics and demonstration sufficiency were
undeclared.

**Decision:** set `EXAMPLES_NEEDED=3`. An eight-slot schedule is consumed as
consecutive four-pair windows: any one pair may be query and the remaining three
are demonstrations. Every cyclic start and query rotation must refute each
listed competitor.

**Alternatives rejected:** rely on a fixed fourth query position, randomly draw
independent examples, or raise the demonstration count without measuring the
actual downstream assembly. Those choices either hide rotation ambiguity or
change episode cost unnecessarily.

**Evidence / limits:** the task-local probe checks 120 windows and 480 rotations;
the Racket census checks 300 production lessons and 1,200 rotations. The rival
family is finite, so “identifiable” means identifiable against those declared
competitors.

## D6 — Remove support depth 4 after exact-axis collision

**Prior choice during this review:** initially broaden support depth to 2..4.

**Reversal:** remove 4 and advertise 2..3 only. On the 10-row horizontal canvas,
depth 4 leaves insufficient transverse room for three distinct `low`, `middle`,
and `high` coordinates; two labels collapse. The failed matrix produced 255
undecodable draws.

**Alternatives rejected:** add a silent geometry-specific remapping, reject
selected calls dynamically, or list a large incompatibility table. None makes
the nominal cross-product cleanly observable.

**Evidence:** the geometric regression failed before the change and passes after;
the final full matrix has zero findings and no declared incompatibilities.

## D7 — Link every semantic witness to the rival it refutes

**Prior choice during this review:** define executable witnesses but omit
`WITNESS_RIVALS`.

**Reversal:** add the explicit mapping. The first strict semantic gate observed
no ambiguous rotations but correctly rejected unscoped witness evidence.

**Alternatives rejected:** weaken the shared gate or rely on matching names. A
machine-checkable relation is safer than naming convention.

**Evidence:** the retained red semantic result and passing rerun; focused tests
verify each firing witness actually disagrees with every named rival.

## D8 — Synchronize selected active authority text, preserve archival raw text

**Prior choice:** canonical `program_solution` was formatted while selected
`target_code` was minified; normalized semantics matched. Why the active copy
was minified is unknown.

**Decision:** copy canonical text exactly into active `racket_target.target_code`
only. Preserve `raw_code` byte-for-byte as archival evidence.

**Alternatives rejected:** ignore exact authority provenance, rewrite both fields,
or alter the rule. Exact selected/canonical binding is useful, while rewriting
raw history would destroy evidence.

**Evidence / limits:** authority sync and execution parity pass. Diagnostics
explicitly report the retained divergent `raw_code` archive.

## D9 — Build one reusable finite-schedule probe

**Decision:** keep `workspace/probe_curriculum.py` as a source-bound tool that
iterates the generator's actual rivals/witnesses, cyclic starts, rotations and
geometry cross-product.

**Alternatives rejected:** hard-code a second list of rival names in a notebook,
or rely only on the 12-lesson semantic smoke test. Both drift easily.

**Evidence / limits:** final probe passes 120 windows, 480 rotations and 168
geometry cases. It uses the Python mirror for speed; Racket census is the
independent authoritative check.

## D10 — Do not modify audit targets

The two assigned audits were evidence-only. Both concrete defects are retained
under `WORK/checks/audit/` and described in `AUDIT.md`; no file under either
audited generator was changed. Suggested repairs are deliberately separated
from the selected-task patch.

## D11 — Treat post-apply source hashing as part of patch replay

The first outer-root replay could not resolve the patch's `repo/...` paths. The
final replay initialized an isolated Git repository at the fresh packet's
`WORK/` directory, ran `git apply --check`, applied the exact packaged patch,
and compared the resulting generator and active-rule hashes with the checked
working copy before running tests.

**Alternative rejected:** accepting `git apply` exit status alone. Depending on
Git root and current directory, out-of-scope hunks can be skipped; a final source
hash is the direct proof that the intended bytes were installed.

**Evidence:** `checks/fresh-replay/apply.log`,
`checks/fresh-replay/task-tests/result.json`, and
`checks/fresh-replay/rule-smoke/result.json`.

## D12 — Keep the approved source fixed and add a task-local ray-relation prototype

**Decision:** leave approved `generator.py`, canonical data, rule hash, and active
fixed-rule path byte-for-byte unchanged. Add an unapproved prototype under
`workspace/parametric/` with one episode-level parameter:
`opposite_opening` (the exact canonical/default Racket source) or
`through_opening` (the same singleton/open-side analysis with the ray direction
reversed). The setting is fixed across all demonstrations and queries.

**Why this parameter:** it preserves the original object roles and inference
pattern while varying one causally meaningful action. Paired settings reuse the
same lawful inputs; three demonstrations refute the sole declared rival and all
four retained queries differ. This is a bounded two-program family, not a claim
against arbitrary learned hypotheses.

**Evidence:** `WORK/checks/parametric/c5a69e7cd8c8-ray-relation-v1/` contains two
exact-Racket episodes, six demonstrations, eight queries, separate public/private
artifacts, exact rules, source bindings, and a hash manifest. Verification passes
with prototype SHA-256
`cf808d05e72b649559dc5b8fcf71f9bbb42732a96f6f7e405f4e625b05a09d56`.
The final focused after suite passes 47 tests in
`WORK/checks/c5a69e7cd8c8-task-tests-final-v3/`.

**Adversarial reversal:** the first writer pretty-printed public JSON after deriving
its ID from canonical compact bytes and emitted the first setting before checking
batch-wide collisions. Tests exposed both mismatches. Final review then showed that
hidden `pairs` could be analyzed independently of visible `train`/`test`, duplicate
report rows could stand in for two settings, and report paths could escape the evidence root, and refreshed manifests could
misstate the report schema, task, approval state, prototype path, parameter contract,
counts, or rule hashes. The retained writer/verifier now writes exact public bytes, preflights
batch identity, binds hidden pairs to the visible episode, requires one unique episode per setting, confines report paths, binds the full
report contract, and rejects refreshed-manifest tampering.

**Limits / next action:** the prototype is proposed and unapproved. Promotion, if
wanted, should use the normal parametric qualification path and independently
review whether `through_opening` is a desirable family member; no production or
training status follows from this return.
