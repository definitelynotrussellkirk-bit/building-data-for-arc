# Working notes: 9e10061f96e5

## Review diagnosis

The selected baseline failed lint, defect lint, and override checks. It lacked a
`RULE_HASH`, advertised dead controls, sampled only 3–5-cell shapes although the
canonical inputs reach 8 cells, sometimes changed the canonical shrink relation,
and had no executable semantic-rival contract.

The first repair exposed a separate authority bug: the active Racket code listed
eight transform expressions but only seven unique operations. It duplicated a
diagonal reflection and omitted the 270-degree rotation. Two of twelve
Racket-backed lessons therefore disagreed with an independently implemented D4
oracle even though all five canonical pairs still passed. The selected canonical
and selected base authority were corrected to enumerate the full D4 group;
archival `raw_code` was deliberately not rewritten. The resulting rule hash is
`788540441b76`.

## Final design

- One honest exact axis: `n_panels` in 2..4; unknown overrides fail loudly.
- Eighteen unique D4 shape classes, including every canonical class and sizes
  3, 4, 5, 6, 7, and 8.
- Every set partition for N=2,3,4, yielding the full 22-output finite codomain.
- A deterministic five-case curriculum with witnesses against identity-only,
  rotation-only, and cell-count-only rivals.
- Full grammar validation, a Python semantic oracle, strict canonical-profile
  checks, declared witnesses/rivals, and lesson-level identifiability checks.

## Final evidence

Generator SHA-256:
`752eb64318030aeb18978e35769a2dadf77ff9e39bbeff4134d25fd10c42be38`.
The final battery passed 12/12 stages. Portable task tests passed 12/12. The
source-bound lesson census materialized 100 lessons in each difficulty band
(300 total, 1,796 unique inputs), with zero ambiguity, hook warnings, or scoring
errors; every declared rival was refuted in every lesson. The workspace probe
also checks every cyclic five-sample start across all bands.

## Limits

This is a finite declared-rival audit, not a proof that no other induction
shortcut exists. The additional 2- and 4-panel cases extend the exact relation
rule beyond the canonical three-panel examples, and the shape grammar remains a
curated finite bank rather than all polyominoes.
## Current reviewer considerations

Source SHA-256: `752eb64318030aeb18978e35769a2dadf77ff9e39bbeff4134d25fd10c42be38`.

# Decisions for 9e10061f96e5

## D1 — Correct the selected rule authority

**Choice.** Replace the duplicated Racket transform with the missing 270-degree rotation in both selected authority locations, then pin the resulting rule hash `788540441b76`. Preserve the archival `raw_code` unchanged.

**Why.** The first repaired generator produced two source-bound lessons whose Racket labels disagreed with the independent Python D4 oracle. The exact counterexample showed two shapes related only through the omitted orientation. Static inspection confirmed eight transform expressions but only seven unique operations. All five canonical examples were too weak to expose this.

**Alternatives rejected.** (1) Make the Python oracle mimic the broken seven-transform relation: rejected because the written task and generator summary explicitly require full D4 equivalence. (2) Restrict the generator to shapes on which the omission is invisible: rejected as distribution laundering. (3) Rewrite archival raw code too: rejected because it is provenance, not selected authority.

**Failure mode/limit.** This establishes parity for the selected authority and all tested inputs, not a formal proof of the Racket implementation. The focused metamorphic regression protects the exact missing-rotation case.

## D2 — Remove false controls instead of simulating them

**Choice.** Keep only `n_panels` as a public exact axis, valid 2..4, and reject unknown override keys.

**Why.** The baseline advertised singleton/dead position and density controls plus helpful textures that were byte-identical to default draws. A narrow honest interface is safer than nominal controllability.

**Alternatives rejected.** Implementing palette/texture aliases merely to silence override checks would add nuisance variation without increasing rule evidence. Retaining diagnostic singleton axes would still burden downstream samplers with non-semantic controls.

**Probe.** The final override stage accepted all 360 exact-control cases and rejected the unknown-key probe.

## D3 — Match canonical object sizes while preserving compact support

**Choice.** Use 18 unique D4 classes: the eight classes appearing in canonical inputs first, then compact additional classes so every occupied-cell count 3..8 has support and at least some equal-size/non-equivalent pairs exist.

**Why.** The baseline’s 3–5-cell bank could not reproduce canonical 6–8-cell profiles. The additional compact classes supply both coverage and counterexamples to cell-count matching.

**Alternatives rejected.** Unbounded random-polyomino enumeration was unnecessary and harder to validate. Canonical-only classes would overfit five examples and reduce nuisance diversity.

**Failure mode/limit.** This is still a finite bank, not all connected shapes. That is intentional for deterministic, auditable generation.

## D4 — Cover the complete finite relation codomain

**Choice.** Enumerate every restricted-growth set partition for N=2,3,4, yielding Bell(2)+Bell(3)+Bell(4)=22 possible relation matrices. Use an arithmetic seed/sample schedule so the fixed linter probe reaches all 22.

**Why.** The first repair produced only eight distinct outputs and failed diversity. Relation partitions are the actual semantic output degrees of freedom, so explicit complete coverage is clearer than hoping random class assignment visits them.

**Alternatives rejected.** Increasing random draws or adding arbitrary noise would not guarantee finite-codomain coverage. Restricting to three panels would match canonical dimensions but unnecessarily narrow a rule that is well-defined for 2–4 panels.

**Failure mode/limit.** Two- and four-panel inputs extend beyond the canonical three-panel demonstrations. They preserve exactly the same pairwise relation rule.

## D5 — Make shortcut counterevidence lesson-level, not merely frequent

**Choice.** Cycle five semantic cases so every five consecutive generated examples contain: non-identity equivalence, reflection-only equivalence, and equal-size non-equivalence. Declare executable rivals and bind each witness to the rival it must refute.

**Why.** Per-sample witness frequency does not guarantee that assembled lessons contain the needed evidence. The production sampler uses five demonstrations; therefore every cyclic five-sample window is the correct unit.

**Alternatives rejected.** Independent random witness selection could leave occasional ambiguous lessons. Hard-coding one matrix per witness would create a matrix shortcut, so relation partitions remain varied within each compatible case.

**Probes.** Task tests cover consecutive windows; `workspace/probe_curriculum.py` covers all five cyclic starts across easy, medium, and hard; the source-bound census checks 100 production lessons per band.

## D6 — Let difficulty skew defaults, never exact support

**Choice.** Use the shared difficulty-aware integer draw for `n_panels`, with easy favoring 2, medium centered on 3, and hard favoring 4. Exact overrides 2, 3, and 4 remain legal in every band.

**Why.** This gives a measurable curriculum effect without making any semantic case or shape class band-exclusive.

**Probe.** At 100 draws per band, observed panel-count means were easy 2.17, medium 3.00, hard 3.70. Exact override observations were 2/3/4 in every band.

## D7 — Validate semantics and grammar independently

**Choice.** Add strict grid checks, panel parsing, D4 canonicalization, a Python relation oracle, canonical-profile checks, semantic witnesses/rivals, and lesson identifiability.

**Why.** Structural validity alone would not have caught the authority bug; semantic comparison alone would not catch malformed separators, colors, or alien shapes. Both are needed.

**Failure mode/limit.** The Python oracle is independent in implementation but shares the intended mathematical specification; agreement across finite probes is strong evidence, not proof.

## D8 — Add a reusable curriculum probe

**Choice.** Add `workspace/probe_curriculum.py`, with its own portable-runtime discovery and JSON output.

**Why.** Future agents need a cheap way to recheck the exact controls, all 22 outputs, difficulty ordering, cyclic lesson windows, witnesses, and rival disagreements after edits. The initial version failed in the isolated task snapshot because child processes did not inherit its import path; the failed run is retained and the final tool locates both source and portable runtimes itself.
