# Compression authority probe

This is an authoring evidence probe. Do not run it during a blind solve.
It imports the selected generator from this checkout, reads only this task's
canonical pairs through `reviewer_support`, and obtains generated and optional
hand-authored reference outputs through public `Catalog.apply` with the canonical
Racket rule. Python competitor outputs are never used as reference labels.

From the review packet root:

```bash
python3 review.py run python3 generators/4e081a15d785/workspace/probe_compression.py --seeds 2 --samples 8 --out ../checks/compression-probe.json --hand-witness --require-witness
```

From a standalone library checkout, omit `python3 review.py run` and select a new
ignored `var/` output path. In a standalone copied runtime without Catalog
metadata, `--library /absolute/path/to/library` selects the Catalog authority;
the probe rejects any generator source hash mismatch.

The report retains exact source/rule identities returned by execution, canonical
shortcut fit, first generated counterexamples for actual declared competitors,
per-band input/output shapes, distinct input counts, strict stripe support,
schedule profiles, and observed integer-control distributions. Deletion counts
reported by the generator are independently compared against Racket output
dimensions. Optional hand witnesses are labeled separately and never satisfy
generated witness coverage.

Seeds are integers `0..N-1`; indices are consecutive `0..samples-1`, in each of
easy, medium, and hard. Reference batches contain at most 64 inputs. Errors and
canonical shortcut misdeclarations yield exit 2 and remain in the JSON report.
The output path must be new, so earlier source-bound evidence is preserved.
Missing contract/witness coverage is explicit; `--require-witness` gives exit 1
for that condition. Finite coverage does not establish universal correctness,
lesson identifiability, approval, or training admission.

## Lawful mutation diagnostics

The companion `probe_lawful_mutations.py` investigates the generic defect lint's
small-shape warning using its exact pure mutation functions. It extracts their
unmodified ASTs from the selected shared source, records the source hash and
function text, and labels six mutations through public `Catalog.apply`.

```bash
python3 review.py run python3 generators/4e081a15d785/workspace/probe_lawful_mutations.py --out ../checks/lawful-mutations
```

Use a new output directory. `input.json`, `racket.json`, `evidence.json`, and
`commands.json` preserve the parent draws, exact mutations, source/rule identities,
validator observations, actual outputs, and invocation. Three genuinely invalid
training-domain examples are checked separately without claiming Racket execution.
The tool reports errors explicitly and does not change the lint result. A future
change to the shared helper dependencies requires reviewing the extraction;
successful diagnostics are evidence for a maintainer's semantic decision, not a
waiver or approval mechanism.
