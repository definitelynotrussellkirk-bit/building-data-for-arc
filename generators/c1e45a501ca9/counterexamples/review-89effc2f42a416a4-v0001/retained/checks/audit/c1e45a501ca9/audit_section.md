## c1e45a501ca9

**A-C1E-1 — Reproduced exact-control defect; findings only, source unchanged.**
The audited generator is version `1.3.0`, SHA-256
`0088b656430fb47933974db0db91df01fdd78fc4e03a60a7e8d406a78306c791`.
The selected Racket authority executed with rule hash `f7ef1caf5361`
and rule-text SHA-256
`28223f52ca8dbb3bf1b7f2a6ea64fd9d1a63753a99b59b47ef0c61eb3de33f2b`.
The actual authority receipt matches the catalog hash. No generator or rule bytes
were edited; the generator hash was checked again after reference execution.

At `seed=0`, `sample_index=0`, `difficulty=easy`, the declared exact override
`n_cells=1` produces **two** colored source cells. Requesting `n_cells=6` also
produces two. Both are byte-for-byte the unoverridden grid. A third controlled
call, `palette_size=1`, still emits two distinct non-guide colors. The unknown
key `typo_axis=123` is silently accepted and also returns the same grid.
Across the five measured calls (baseline plus four probes), all five pass
`self_check`, all five have the same input, and all five record an empty
`overrides_used()` dictionary. This is **one unique 6×7 input**, not five
independent examples.

The source draws only `grid_h` and `grid_w` through the keyed context. It chooses
`n_seed` directly with the layout RNG, never reads `n_cells`, and uses a fixed
eight-color source palette. Thus these accepted controls cannot make their
advertised changes. The `n_cells=1` lower bound also conflicts with the validator's
requirement for at least two source cells. A repair should honor or remove each
advertised control, reject unknown keys, and reconcile count bounds with the
validator. The retained public-loader probe records actual draw provenance.

The supported `arcpuzzles apply` command returned a valid output for **1/1
unique input**, with no execution error. It mirrors both source cells while
preserving the originals. This establishes the witness's actual reference
label; it does not repair the exact-control defect or constitute a semantic-gate
pass. The witness is an ordinary generated input and belongs to the documented
restricted generator domain. `rival_output` is explicitly null because requesting
one source cell specifies an input constraint, not a unique alternative output
grid; no rival-rule disagreement is claimed.

**Inherited lead versus current measurement.** The current review index already
retains this source-bound `n_cells`/unknown-key issue from
`review-9a3cfcbadd2ba12e:v0001` (`unresolved`) and
`review-31118be85ee0aad5:v0001` (`needs_triage`). Those records prompted this small
reproduction. The five calls and reference output above were run afresh in this
assignment; the finding remains unrepaired. The upper count and palette-size
probes add concrete control observations on the same source.

**Domain question, not a new label-defect claim.** A separate validator-only
inspection of all five labelled canonical pairs (variant 0: four train and one
test) accepts **2/5**. Train pair 1 has below-guide source cells; pair 2 clips
reflections at the boundary; pair 3 has both properties. These are rejected by
the generator's documented left/upper, fully in-bounds restriction. The selected
rule handles either side and bounds-checks reflected coordinates. Decide whether
this narrower sampling domain is intentional when repairing the target. These
canonical labels were read as authoring evidence, not rerun through Racket in
this audit, and the observation is not a claim of a new semantic counterexample.

**Evidence and limits.** Reproducer, five observed calls, input, actual reference
output, source/rule hashes, and exact commands are retained here:

- `checks/audit/c1e45a501ca9/reproduce.py`
- `checks/audit/c1e45a501ca9/counterexample.json`
- `checks/audit/c1e45a501ca9/input.json`
- `checks/audit/c1e45a501ca9/racket.json`
- `checks/audit/c1e45a501ca9/commands.json`
- `checks/audit/c1e45a501ca9/probe.log`
- `checks/audit/c1e45a501ca9/apply.log`
- `checks/audit/c1e45a501ca9/finalize.log`

All three recorded commands exit 0; the probe exits successfully when the stated
defect is reproduced. No task-test stage, semantic gate, random census, lesson
assembly, or query-rotation check was run. Production lesson identifiability,
rotation identifiability, and universal generator validity remain **unknown**.
This finite audit supplies an actionable defect, not a green audit certification.
