## 109a03554ed3

**A109-1 — Reproduced teaching defect, reaffirming the retained unresolved finding.** The declared four demonstrations can leave “stamp the union” indistinguishable from the intended anchored symmetric difference. Fresh public Racket application confirms the existing finding `review-1b19c8c442bcce16:v0001` on the same generator bytes. The audit target was left unchanged.

### Exact source and scope

- Generator: `generators/109a03554ed3/generator.py`, version `2.1.0`, SHA-256 `7a50a0aa6de465c297a44eec99a67a85e944091c2f527d76af39a9035f3d7623`.
- Canonical `program_solution` text SHA-256: `93eb170bbac9335efb8ee6dc74f009ad14846b22e4017df5e8412ef8aaf2d7fb`; whitespace-normalized SHA-256: `cdb228903872bd8e2e8137798f9eb7cf3992debd19b407293ea7a950d6bb72a5`.
- Public apply reports executed rule hash `cdb228903872`, matching its catalog hash; its executable rule-text SHA-256 is `e6bd293fdd9ab613f9f469f68e51145574c8a3edde618e9838bfe2cf5c7c5210`. Both text identities are retained separately.
- **One explicitly assembled lesson; five unique inputs:** seed `0`, difficulty `medium`, no overrides, demo sample indices `1,2,3,4`, query index `5`. This is a bounded replay of a known witness, not a random census.

The generator declares `EXAMPLES_NEEDED = 4` and comments that at least one demonstration refutes the union rival. The audited lesson uses consecutive sample indices. Neither an executable `CANONICAL_SHORTCUTS` nor `LESSON_COMPETITORS` declaration exists in this source. The union rule below is an investigator-defined lesson competitor; no claim is made that it fits all canonical examples.

### Measured result

An independent component parser identifies each source and its maroon anchor, converts its colored cells to relative offsets, and renders either the union or symmetric difference on a zero canvas at cyan. Public `arcpuzzles apply` supplied the actual Racket outputs.

| Sample index | Role | Shared source offsets | Union matches Racket |
| --- | --- | ---: | --- |
| 1 | Demo | 0 | Yes |
| 2 | Demo | 0 | Yes |
| 3 | Demo | 0 | Yes |
| 4 | Demo | 0 | Yes |
| 5 | Query | 1 | No |

All **5/5** inputs pass `self_check`; all **5/5** public Racket outputs are valid; the independent XOR renderer matches Racket **5/5**. All inputs are ordinary generator outputs with no manual edits, so this is within the documented generation domain.

For query index `5`, red offsets are `{(-1,0),(1,0)}`, blue offsets are `{(1,0),(2,0)}`, and the shared offset is `(1,0)`. The union paints one extra green cell at zero-based grid coordinate **(10,9)**; Racket leaves that cell **0**. All four demonstrations lack shared offsets, so they supply no evidence that distinguishes these two rules.

### Evidence, disposition, and limits

`checks/audit/109a03554ed3/union_survivor_witness.json` retains every exact input, validator result, source offsets, actual Racket output, union-rival output, input/output hashes, and query difference. `racket.json` is the unmodified public apply receipt. `audit_union.py` is the replayable independent probe; `RESULTS_fragment.json` records all three substantive commands with argument arrays, working directory, exit status, timing, and retained logs.

All three commands exited **0**, and the comparison command confirms that the defect reproduces. That successful reproduction is **not a semantic pass**. No combined gate, broad battery, random sweep, or query rotation was run; rotation verdict is **unknown**. This finite witness establishes the failure of the stated four-demo guarantee under the explicit consecutive-index assembly, without estimating its frequency or certifying other lesson assemblers.

**Recommended target-local follow-up:** guarantee an overlap witness within every supported four-demo lesson and register an executable union competitor so the teaching requirement is checked. The finding remains open; this findings-only audit includes no target-source patch.
