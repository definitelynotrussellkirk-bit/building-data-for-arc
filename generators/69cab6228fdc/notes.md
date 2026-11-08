# Working notes: 69cab6228fdc

## Current review decision

Keep production version `2.1.0` and canonical rule `8fec6004f588` unchanged.
The production source still has SHA-256
`e321c1876f90a5efb13c60f8eb3c32f4f89d9d74121695b1ce6c3fe9f1c801a2`.
No open source-bound audits were listed in the issued review index.

The concrete repair is to `workspace/passthrough_probe.py`: an explicitly empty
canonical evidence list previously returned `status=pass` and `fits_all` for
both shortcuts after zero comparisons. It now fails and reports `unverified`.
The report separately marks canonical evidence `checked`, `empty`, or
`not_provided`; intentionally omitted evidence remains a generated-scene-only
check. Nonempty refuting evidence still fails. Production sampling, validation,
semantic rivals, and authority are unaffected.

Fresh evidence under `checks/69cab6228fdc/` belongs to assignment
`review-5bbd1c7f3c08fb63`: three focused regressions fail on the original probe
and pass after repair (`probe-red/`, `probe-green/`); the isolated task stage
passes 12 tests with no skips (`task-tests/`). The 3.426-second bounded audit
checks eight evidence-integrity cases and 576 joint override/palette boundaries,
with no unexpected failures (`adversarial-v2/report.json`). Ten actual canonical
Racket executions agree with their expected labels and the Python mirror: all
five canonical pairs, the exact two-unmapped-color witness, and four selected
boundary inputs (`adversarial-v2/racket.json`). Exact commands and results are
retained in the command receipts and the replayable `check_boundaries.py`.
The older battery/census totals below are inherited evidence, not fresh reruns.

## Leads and baseline

Prior note `GNOTE-002795` correctly identified that canonical examples do not
teach unmapped-color passthrough and introduced the A/P/P/A three-demo schedule.
I treated that note as a lead, not as current evidence. The fresh baseline
battery was 12/12 green, while the required portable task-test stage failed
1/12 because its canonical-data path depended on source-tree depth.

## Current root causes

1. The selected test guessed `data/canonical` and `data/base` locations instead
   of using `reviewer_support`; this broke after isolated relocation.
2. Version 2.0.0 emitted zero or exactly one unmapped color. Across 400 draws per
   band, a `first_unmapped_only` rival fit every generated input and all five
   canonical pairs. The exact two-color witness was rejected by `self_check`.

## Repair

Version 2.1.0 permits up to two passthrough colors, guarantees two on each
default scheduled present branch, declares the one-only rival and witness, and
caps only default present draws to at most three legend pairs so two unused
colors exist. Explicit four-pair overrides remain supported with one unused
color. Portable tests now use `find_root` and `canonical_pairs`.

The task-local `workspace/passthrough_probe.py` dynamically checks declared
canonical shortcuts, cardinality, rival refutation, all requested cyclic lesson
starts, and the exact witness.

## Final evidence

- Generator SHA-256:
  `e321c1876f90a5efb13c60f8eb3c32f4f89d9d74121695b1ce6c3fe9f1c801a2`
- Battery: 12/12 green (`checks/after-final/`).
- Portable task tests: 18/18 (`checks/task-tests-final/`).
- Lesson census: 300/300 lessons unambiguous against declared rivals, 1,200
  unique inputs (`checks/lesson-census-final.json`).
- Task-local probe: 300 samples and 300 cyclic windows, zero failures
  (`checks/passthrough-probe-final-v2.json`).
- Racket authority unchanged; exact two-color witness agrees with Racket
  (`checks/shortcut-witness/`).

## Limits

Default lessons teach two unused passthrough colors. The validator does not yet
cover more than two simultaneous passthrough values or target colors appearing
in the body, so finite rival success is not a universal identifiability proof.
## Current reviewer considerations

Source SHA-256: `e321c1876f90a5efb13c60f8eb3c32f4f89d9d74121695b1ce6c3fe9f1c801a2`.

# Design decisions for 69cab6228fdc

## D1 — Preserve the selected authority

The canonical Racket rule and all five canonical labels were already coherent.
The defect was in the Python generator distribution and its portable tests, not
in the authority. I retained `RULE_HASH=8fec6004f588`; rule smoke and authority
sync are green in `checks/after-final/`. No canonical or Racket source changed.

## D2 — Replace guessed canonical-data paths with the supported helper

The selected task test used `Path(__file__).parents[1]` to guess where
`data/canonical` lived. The required isolated task-test stage snapshots tests in
a different layout, so the guess produced one failure despite the ordinary
battery being green. The repair uses `reviewer_support.find_root` and
`canonical_pairs`, which are explicitly designed for the portable runtime.

Rejected alternatives:

- Copy canonical data into the task folder: duplicates authority and creates a
  synchronization problem.
- Add more parent-depth guesses: still layout-dependent and brittle.
- Delete the canonical assertions: removes useful source-binding coverage.

Evidence: failing `checks/task-tests-before/`, passing
`checks/task-tests-portability-fix/`, and final `checks/task-tests-final/`.

## D3 — Teach more than one passthrough value

Version 2.0.0 scheduled mapped-only and passthrough demonstrations, but every
passthrough scene contained exactly one unmapped nonzero color. Across 400 draws
per band, the histogram was `{0:200, 1:200}`. Therefore the wrong rule “preserve
only the first unmapped color” fit all 1,200 generated draws even though it
disagrees with the intended identity fallback when two unmapped colors occur.
The old validator also rejected the exact two-color witness.

Version 2.1.0 samples two distinct unused colors on every default `present`
branch, places each at least twice, permits and reports both in `_analyze`, and
adds the rival plus an executable witness to the semantic contract. The same
1,200-draw probe then produced `{0:200, 2:200}` in each band and no surviving
present-branch rival. The exact witness changed from rejected to accepted.

Rejected alternatives:

- Merely declare the new rival without changing generation: the rival would
  survive every lesson.
- Add a second color probabilistically: pooled frequency would not guarantee
  that every complete three-demo lesson contains a distinguishing witness.
- Rely on a single hand-built regression: it would validate the rule but not the
  production sampler.

Evidence: `checks/multi-passthrough-before.json`,
`checks/multi-passthrough-after.json`, and the red/green task-test runs under
`checks/task-tests-multi-red/` and `checks/task-tests-multi-green/`.

## D4 — Reserve palette capacity only for default teaching draws

Four legend pairs consume eight of the nine nonzero ARC colors, leaving only one
unused color. To guarantee two passthrough values in production lessons, the
default scheduled `present` branch caps the sampled pair count at three. The
ordinary `absent` branch retains the full 2–4 range and the linked canonical
prior. An explicit `n_pairs=4, passthrough=present` override remains lawful and
observable, but can expose only one unused passthrough value.

I rejected globally removing four-pair scenes because that would needlessly
shrink the advertised exact API and generalized mapped-only distribution. The
teaching guarantee is explicitly attached to default lesson generation, not to
every user-pinned combination.

## D5 — Make the investigation reusable

`workspace/passthrough_probe.py` is a standard-library task-local probe. It:

- iterates the generator's actual `CANONICAL_SHORTCUTS` declaration and verifies
  each shortcut fits every canonical pair;
- checks passthrough cardinality and source-bound schedule behavior per band;
- confirms every declared canonical shortcut is refuted by each default
  `present` draw;
- tests all requested cyclic starts of the three-demo lesson window; and
- retains the exact two-color counterexample.

The tool was developed red/green against the isolated task-test snapshot. Its
final 100-sample-per-band run found 0 failures and 0 ambiguous windows; see
`checks/passthrough-probe-final-v2.json` and the final 18-test result.

## D6 — Production census and solve policy

The production lesson census used the shared sampler with 100 lessons per band,
three demonstrations and one query per lesson. It materialized 400 pairs and 400
unique inputs per band (1,200 globally), reported no errors, and refuted every
declared rival in all 100 lessons of each band. This is stronger than individual
witness counts because it evaluates complete lessons, but remains a finite
rival census.

The post-repair solve was prepared from generator SHA-256
`e321c1876f90a5efb13c60f8eb3c32f4f89d9d74121695b1ce6c3fe9f1c801a2`.
I declared earlier rule exposure and did not consult the reference during the
solve. One implementation passed all three visible examples; no artificial
negative revision was created.

## D7 — Known limits and self-review

The repair guarantees two unmapped **unused** colors in default present scenes,
not arbitrary numbers or every possible non-source category. The validator caps
passthrough values at two and rejects legend target colors in the body. Thus the
return does not claim universal coverage of every lawful identity-fallback
case; a contrived “preserve at most two” rule or target-specific fallback is
outside the tested generator domain.

This limit is deliberate scope control, not evidence that those broader cases
are impossible. A future extension should add a separately scheduled broad
fallback profile and rerun override compatibility, cyclic lesson tests, the full
battery, and the source-bound census rather than silently increasing body
cardinality.

## 2026-10-25 native promotion candidate

The current native candidate is `workspace/parametric/adapter.py` with
`recolor_scope=all_sources|most_frequent_source`. The default is byte-identical
to the selected canonical program. The alternative counts input-body source
frequencies, recovers one unique most-frequent source, and then applies only that
source's paired target mapping. Matched inputs, visible passthrough colors, and
varying selected legend positions teach the episode-fixed setting.

The family supports 2–6 demonstrations and four prefix-stable queries; query 4
is exact 30×30. Protected-Racket self-review tested the other setting plus
first-source, last-source, least-frequent-source, largest-source-color, and
zero-unmapped rivals with no query-changing demo survivor in the retained
bounded audit. The retained causal counterfactual substitutes the first legend
source for the recovered frequency winner and changes the final output.

This is reviewer-ready promotion evidence only. Owner exact-source acceptance
and any training admission remain pending.

Owner reconciliation: keep both exact recolor-scope programs and add the
independently returned mapped-region relay as a third disjoint rule. The
canonical default, production generator and original sampler/validator remain
unchanged. The common sampler deliberately extends the input grammar to allow
existing target-color cells and three passthrough colors; all three rules share
inputs and the frequency winner varies. Current owner evidence:
`evidence/owner-variant-reconciliation/current.json`.
