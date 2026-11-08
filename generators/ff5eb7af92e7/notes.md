# Working notes: ff5eb7af92e7

## 2026-10-07 review

- Kept the canonical Racket rule unchanged and pinned `RULE_HASH=f3fbafdf1862`.
- Replaced misleading/no-op controls with exact, observable `grid_h`, `grid_w`,
  `active_rows`, and `n_distinct_colors` axes.
- Added scheduled canonical profile anchors and broad/dense generalization.
- Every ordinary draw includes a strict 2/1/1 three-color plurality row. This
  refutes the strongest canonical-fitting absolute-majority shortcut plus
  exact-three, at-least-three, and two-colors-only rivals.
- Kept `strict_canonical_like` as the lawful canonical domain predicate; teaching
  requirements remain separate executable `SEMANTIC_WITNESSES`.
- Added regression tests and `workspace/probe_schedule_phases.py` for finite
  phase replay with canonical Racket labels.

Limits: declared-rival and finite-phase checks do not prove universal
identifiability, and the phase probe uses one representative seed per phase.
Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `cf3388ee077f512b258be1855ac812d0009a297150af8bd807c9f582ae929ad3`.

# Decisions

## D1 — Keep the authoritative transformation unchanged

**Choice.** Leave the canonical Racket row filter untouched and pin its normalized
hash as `RULE_HASH = "f3fbafdf1862"`.

**Rationale.** All four canonical input/output pairs agree with the existing rule,
the before battery's rule smoke and authority checks were already green, and the
observed defects were in sampling, controls, validation, and teaching support.
Changing the rule would have expanded scope without evidence of a label defect.

**Alternatives rejected.** I did not rewrite the rule to require an absolute
majority or mode count three; those are precisely the canonical-fitting shortcuts
the repaired distribution must refute. I also did not broaden the authoritative
domain to arbitrary tied rows because no canonical example or written task
requirement establishes a desired tie curriculum beyond the current program's
leftmost implementation detail.

**Probe / limit.** Final rule smoke, Racket lint, and authority sync are green in
`checks/after/`; the exact shortcut witness is separately executed by public
Racket `apply` in `checks/shortcut-answer/racket.json`.

## D2 — Replace the advertised axis surface rather than preserve aliases

**Choice.** Expose only four exact pixel-observable controls:
`grid_h=5..12`, `grid_w=7..14`, `active_rows=2..12`, and
`n_distinct_colors=3..9`. Reject every retired or unknown key, and declare
`active_rows > grid_h` as an explicit dependent incompatibility.

**Rationale.** The baseline accepted controls that were ignored, aliases, locked
constants, or capable of returning grids that contradicted `self_check`. A smaller
truthful interface is safer for downstream callers and easier to test than a broad
fictional interface.

**Alternatives rejected.** Implementing palette names, position bias, density,
and seven texture values would add task-irrelevant knobs and retain several
ambiguous semantics. Silently accepting them as aliases would preserve the defect.

**Probe / failure modes.** Task tests round-trip all four controls in every band,
reject retired and invalid inputs, and verify observation from returned pixels.
The full override matrix passes with zero findings and rejects unknown keys.
The finite contract still does not promise every joint value when
`active_rows > grid_h`; that case is intentionally incompatible.

## D3 — Use linked profile phases with canonical anchors

**Choice.** Cycle `canonical_profile → broad → dense` using
`(seed + sample_index) mod 3`. Canonical-profile draws schedule the four original
shape/palette profiles while still randomizing row positions, colors, and layouts.

**Rationale.** The profile-floor gate requires real support for canonical sizes and
palette breadth, but repeatedly returning fixed canonical identities would harm
diversity. A linked phase gives each consecutive four-pair lesson all profile
classes and makes every start phase testable.

**Alternatives and failed attempt.** An initial schedule depended only on
`sample_index`; the linter's fixed-index, varied-seed census then saw only one
phase. Moving the phase key to `seed + sample_index` preserved consecutive lesson
coverage while exposing every phase to independent seed probes. The retained
finite-phase probe checks all 3 starts × 3 bands.

**Limit.** The probe exhausts the declared finite phase, not all seeds or grid
identities. Canonical anchors are distributional anchors, not copies of canonical
examples.

## D4 — Make integer draw provenance match the public ranges

**Choice.** Use bounded integer draws for general `grid_h`, `grid_w`, and
`active_rows`, and a strict full-range integer draw for `n_distinct_colors`.

**Rationale.** Integer-valued `draw_choice` varied pixels but did not contribute
bounded integer provenance, so the defect linter reported only the exact anchor
values `[6,6]`, `[8,8]`, `[4,4]`, and `[8,8]`. The source should express both the
actual distribution and its range in the draw API.

**Alternatives rejected.** Weakening the linter or narrowing the declared axes to
one anchor would hide real general variation. Keeping weighted choice lists would
leave the same provenance ambiguity.

**Evidence.** `checks/defect-lint2/` retains the warning; `checks/defect-lint3/`
and the final battery are clean. This experience motivates feedback F1.

## D5 — Put a decisive plurality witness in every ordinary pair

**Choice.** Every ordinary input contains a row with counts `2/1/1` across three
nonzero colors. A second witness row exercises broader palette participation, and
remaining rows vary mode counts, density, color roles, and positions.

**Rationale.** The canonical demonstrations all fit four simple rivals:
absolute-majority-only, exactly-three, at-least-three, and two-colors-only. A
`2/1/1` row is the smallest lawful strict plurality that contradicts all four at
once while remaining easy to inspect.

**Alternatives rejected.** Rare random witnesses would not establish lesson-level
teaching support. Degenerate or validator-only counterexamples would not repair
production lessons. One special lesson per band would leave arbitrary starts
underspecified.

**Probe / limit.** The semantic census observed each witness in 600/600 draws; the
larger lesson census refuted every declared rival in 300/300 production lessons
and all 1,200 rotations. This is finite evidence against named rivals, not a proof
against every possible induction rule. Requiring the witness in every pair also
creates a visible regularity of its own, documented in the self-review.

## D6 — Separate domain membership from teaching support

**Choice.** Define `strict_canonical_like` as the lawful strict-mode domain
(`self_check`) and keep anti-shortcut requirements in `SEMANTIC_WITNESSES`.

**Rationale.** A first implementation combined the two and therefore rejected all
four canonical inputs solely because they lacked the new teaching witnesses. A
domain predicate must accept canonical examples; a curriculum predicate may demand
additional support in generated lessons.

**TDD sequence.** The failed semantic battery is retained in
`checks/after-semantic-boundary-fail/`. I added a regression asserting canonical
acceptance, observed it fail in `checks/task-tests-red4/`, then made the minimal
boundary change and reran the focused and full suites.

## D7 — Three ordered demonstrations plus one query

**Choice.** Retain `EXAMPLES_NEEDED = 3` and test consecutive production bundles
with indices `[start, start+1, start+2]` as demonstrations and `start+3` as query.
Also test every hold-one-out query rotation because downstream assembly may rotate.

**Rationale.** Each pair already carries all declared witnesses, so three examples
are more than sufficient for the named rivals and match the original canonical
training count. Increasing the count would add cost without addressing a measured
ambiguity.

**Evidence.** The production census reports 0/300 ambiguous lessons. Required
rotation evidence reports 0/1,200 ambiguous rotations; the smoke gate reports
0/48. The local phase probe reports 0/9 production and 0/36 rotated ambiguities.

**Limit.** The census rotation operation reuses each four-pair bundle; it does not
enumerate new random draws. The local probe covers all finite schedule phases but
only one representative seed per phase.

## D8 — Build a reusable phase probe for future agents

**Choice.** Add `workspace/probe_schedule_phases.py` and document its public
wrapper command.

**Rationale.** The shared census deliberately does not enumerate every cyclic
schedule start. This task has a tiny, declared period, so a task-local tool can
close that gap cheaply while obtaining labels from supported Racket `apply`.

**Behavior.** The probe iterates the generator's actual `LESSON_COMPETITORS`,
records source/rule hashes, validates all grids, checks the production query and
all rotations, and states its finite-domain limitations. It does not use private
runner functions or claim approval.

## D9 — Preserve genuine failures and source identity

**Choice.** Keep red task-test snapshots, linter warnings, the semantic-boundary
failure, and checkpoint/resume records. Freeze the exposed solve only after the
final generator hash was established.

**Rationale.** These failures explain why the final design differs from earlier
iterations and prevent a green-only narrative. The solve summary binds the final
generator bytes and honestly declares earlier rule exposure; the blind solve
remains separately marked unexposed.

**Prior evidence.** No prior return ZIP was used. Current queue metadata and notes
were leads, not measurements. In the `8922fefc96ff` audit, a prior unverified index
was used only to identify a branch worth testing; all reported counts and Racket
outputs were independently reproduced from the assigned source hash.
