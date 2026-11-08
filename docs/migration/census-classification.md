# Generator compatibility results

The [complete v0.3 census](census-evidence/receipt.json) ran from a normal wheel
with `/home` reads denied. Each of 3,941 generators was asked for one train and
one test pair at seed17, medium difficulty. The comparison uses the retained
historical runner and authorities, not execution of the predecessor checkout.

| Outcome | Count | Interpretation |
|---|---:|---|
| Equal | 3,911 | Identical measured input/output pairs, including all 449 approved generators |
| Current only | 21 | Twenty native generic programs work without a module-level `PROGRAM`; one historical per-puzzle rule emits rejected identity pairs |
| Historical only | 2 | Missing or failing canonical authority; explicit archival access preserves the older route |
| Different | 4 | Two differing rule authorities; two self-checks reject samples the old runner accepted |
| Both failed | 3 | Generic gather programs emit bare expressions; v0.5 now supports and verifies this format |

Every non-equal outcome is unapproved. None of these measurements changes a
safety label or proves correctness across all seeds, difficulty bands or overrides.
The original JSONL/logs and worker/wheel hashes remain immutable evidence of v0.3.

## Authority cases

- `7c7796f15a18`: no canonical program exists. Explicit archival execution
  reproduces the measured historical pairs.
- `defba1ab4f90`: canonical execution fails with `zero?` receiving `#f` and
  exhausts its attempt bound. Explicit archival execution reproduces the measured
  historical pairs. This does not establish that either rule is semantically right.
- `83edd318e70a` and `9d46a0f24d04`: canonical and archival rules produce
  different outputs. Their historical pair hashes are retained in regression tests;
  the default continues to use canonical authority.
- `deb310c21d0c`: canonical generation succeeds. The historical rule exhausts
  ten attempts; a subsequent explicit archival diagnostic recorded
  `validate.output_equals_input` for every attempt. Identity admission was retained.

## Self-check cases

`c55491432288` rejects sample0 because pivot count3 is outside [1,2]. Its existing
unsafe label remains unsafe. `d982cffd80f8` rejects sample0 and further draws
because its medium band requires exactly two fillable hollow-ring centers.
Canonical and archival rule hashes for the latter are identical. These are
sample-admission differences; bypassing the checks would conceal generator
findings. The explicit archival route retains both checks.

## Generic programs

Twenty current-only generic generators emit their program per task; the old
runner stops while looking for a module-level `PROGRAM`. Their full identities
and errors are retained in `census-evidence/results.jsonl`.

The three `generic_gather_gen1/2/3` generators also emit their program per task,
as a bare expression rather than `(rule! ...)`. v0.5 adds the equivalent wrapper
at the API boundary, retains the original expression and hashes the executable
rule. Racket must still reproduce every supplied pair. No generator source was
changed. Tests cover each generator at seeds0/easy,17/medium and42/hard.

The v0.5 targeted checks supplement the original census; they are not a second
full-corpus census. The four historical-authority pair comparisons and both
self-check cases are in `tests/test_archival_reference.py`; expression support is
in `tests/test_generic_expressions.py`.
