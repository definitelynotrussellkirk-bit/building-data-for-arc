# Working notes: 91c488d9ffdc

## Review repair (version 3.0.1)

The imported generator's rule labels were correct, but its generation contract
was not reliable enough for training use: several public controls were inert or
misleading, unknown keys were accepted, many declared override combinations
were rejected, rectangle placement could silently under-deliver `n_rects`, and
there was no executable semantic curriculum contract. The canonical Racket rule
was already correct and was not changed.

The selected implementation now:

- pins canonical authority with `RULE_HASH = 515ca330e152`;
- exposes only exact `grid_h`, `grid_w`, and `n_rects` controls;
- constructs the requested number of pairwise-border-disjoint rectangles rather
  than retrying and dropping failures;
- keeps all five canonical linked profiles in its anchor schedule;
- uses a three-slot ordered curriculum—canonical-positive, negative, mixed—to
  refute the positive-diagonal-only shortcut;
- provides executable mirrors, semantic observables, witnesses, rivals, and a
  lesson-identifiability hook;
- gives difficulty bands an observable palette effect without changing the rule;
- rejects unknown or incorrectly typed override values.

`workspace/probe_schedule_windows.py` is a reusable deterministic authoring tool
for exhaustively checking consecutive schedule starts against the declared
rivals. It complements the shared random lesson census and query-rotation tests.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `cd8e5459153d6c26d65a65143f12d2f398cf1c596b038f53c34f8fc27d397aa8`.

# Decisions for `91c488d9ffdc`

## D1 — Preserve the Racket authority

**Input evidence.** The before battery's rule smoke, grammar, Racket lint, and
authority synchronization were green. Canonical outputs agreed with the intended
“pair of opposite corners → hollow rectangle border” operation.

**Decision.** Keep the canonical Racket row byte-for-byte unchanged and pin it in
Python as `RULE_HASH = "515ca330e152"`.

**Rejected alternative.** Rewriting the authority merely to match generator
implementation details would add needless label risk. The defect was in data
generation and its contract, not the rule.

**Failure mode watched.** A future authority edit without a corresponding pin
update. Rule smoke and authority sync cover it.

## D2 — Replace broad decorative axes with three exact controls

**Input evidence.** The imported generator declared numerous texture/shape
controls that were inert or only partially honored, accepted unknown keys, and
rejected thousands of advertised combinations.

**Decision.** Expose only `grid_h`, `grid_w`, and `n_rects`; validate strict Python
integer types and bounds, and reject unknown keys. Every joint combination is
constructible, so no incompatibility table is needed.

**Rejected alternatives.** Keeping aliases as “diagnostic” controls would retain
an unnecessary public surface. Silently clamping a requested value would make
provenance disagree with the actual grid.

**Probe.** The exact override matrix accepted 8,100/8,100 draws with zero findings,
and the task tests compare requested values to `observe_overrides`.

## D3 — Construct layouts instead of retrying placement

**Input evidence.** The prior retry loop could exhaust attempts and return fewer
rectangles than `n_rects`, which is especially damaging when provenance claims the
requested count.

**Decision.** Use deterministic constructive families for one to three rectangles,
including corner-separated and nested layouts, and verify pairwise-disjoint border
sets before returning.

**Rejected alternatives.** Raising the retry limit only lowers, rather than
eliminates, the probability of silent under-delivery. Resampling until success
would also make exact-control behavior harder to reason about.

**Failure modes watched.** Border intersection, endpoint collision, accidental
third copies, too-small boxes, and count mismatch. Structural tests include all of
these impostors.

## D4 — Retain linked canonical morphology explicitly

**Input evidence.** The five canonical inputs span heights 7–10, widths 9–12,
and one or two rectangles, including nesting. A pure generic sampler could pass
labels while drifting away from those linked profiles.

**Decision.** Encode the five canonical geometry signatures as scheduled anchor
profiles. The positions/colors vary while linked dimensions and box sizes remain
represented. The strict floor is 20%, and the measured rate was 191/600 (31.8%).

**Rejected alternative.** Copying canonical grids verbatim would reduce diversity
and invite memorization. Broad random dimensions alone would not guarantee linked
profile support.

## D5 — Use a three-slot teaching cycle

**Input evidence.** Every canonical pair uses a positive diagonal, so the plausible
shortcut “only draw rectangles for positive-slope pairs” fits all canonical
examples. A lesson made only from such anchors can be perfectly labelled yet teach
the wrong rule.

**Decision.** Set `EXAMPLES_NEEDED = 3` and cycle:
canonical-positive → negative → mixed/multi. Production uses consecutive ordered
demonstrations and the next consecutive query.

**Rejected alternatives.** Randomly hoping for a negative example does not provide
a per-lesson guarantee. Two demonstrations can refute the diagonal shortcut but
are less robust against first-pair/global-box alternatives. Four demonstrations
add cost without distinguishing another declared rival for this task.

**Probes.** The 300-lesson census found 0 ordered and 0 rotated ambiguities across
1,200 query rotations. The task-local exhaustive probe checked 54 consecutive
starts and found 0 unidentifiable windows.

## D6 — Declare executable rivals and witnesses

**Decision.** Add a pure Python rule mirror, semantic observables, seven witnesses,
six lesson competitors, witness-to-rival claims, and a lesson-identifiability hook.
This turns “the data looks varied” into an executable contract.

**Alternatives considered.** Prose-only notes are cheap but cannot block regression.
Comparing outputs only to Racket establishes label correctness, not whether the
visible demonstrations distinguish a plausible wrong rule.

**Limit.** The rival set is finite. Passing it is evidence of improved teaching,
not a proof of universal identifiability.

## D7 — Give difficulty a small, observable, semantics-neutral effect

**Input evidence.** The first repaired draft left difficulty labels cosmetic; the
defect linter correctly flagged dead bands.

**Decision.** Easy uses colors 1–4, hard uses 5–9, medium uses all nonzero colors.
All bands share geometry profiles and transformation semantics.

**Rejected alternatives.** Restricting hard to larger grids would break exact
canonical-profile hits in that band. Altering rectangle counts by band could also
entangle difficulty with the curriculum phase.

## D8 — Build a reusable consecutive-window probe

**Decision.** Add `workspace/probe_schedule_windows.py`, with a regression test.
It enumerates starts, materializes demonstrations/query, lists surviving declared
rivals, and can fail CI with `--require-identifiable`.

**Why task-local first.** It is immediately useful and source-bound here, while the
shared-tool version needs policy choices for nonperiodic and intentionally ordered
curricula. The corresponding shared recommendation is F1 in
`FEEDBACK_TO_CODEX.md`.

## Remaining limitations

- The schedule is periodic and ordered; random reassembly is not the declared
  production policy, although every recorded query rotation passed.
- Declared rivals do not exhaust all possible ARC programs.
- The override matrix proves controls at sampled seeds, not all integers.
- The checker rejects malformed scenes rather than assigning them semantics; such
  scenes are outside the documented generation domain.
- No Racket or canonical-data change was made, so this return does not broaden the
  underlying rule domain beyond lawful opposite-corner pairs.

## Parametric reviewer build — anchor-area rectangle relay (2026-10-25)

**Choice.** Preserve `all_rectangles` as the byte-exact canonical default and add `anchor_area_select`. The variant reconstructs all same-color diagonal endpoint rectangles, orders them by top-left position, retains the first rectangle's area `A`, selects candidate `(A - 1) mod n`, and draws only that candidate's border in its own input color.

**Why this is a real sequential dependency.** The selected output rectangle is unknown until the anchor is reconstructed and measured. A protected-Racket off-by-one counterfactual uses `A mod n`, selects a different candidate, and changes 46 final cells on an exact qualified query.

**Adversarial repair.** The first bounded sweep exposed a genuine teaching collision: numeric color ordering accidentally agreed with spatial ordering for two-demo lessons at seeds 17 and 101. The generator now uses seed-varying palettes with a safe relative color-order schedule that constructively separates those rules. The repaired sweep covers seeds 0, 17 and 101 and demo counts 2–6: 30 episodes, 300 declared-rival checks, 120 masked public projections, 30 substantive 30×30 cases, 44 protected-Racket evaluations, and zero surviving query-changing rival.

**Qualification.** Native qualification passed both settings at seeds 0 and 17 (4/4 jobs, 40 protected-Racket evaluations). This is reviewer-reported ready evidence only; exact-source owner acceptance and any training admission remain separate.
