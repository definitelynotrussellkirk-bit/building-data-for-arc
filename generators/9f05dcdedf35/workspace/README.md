# Workspace: 9f05dcdedf35

The selected v1.4.1 implementation is `../generator.py`; workspace helpers do not
select drafts or alter the unchanged Racket authority (`85fa63b64c3c`). Current
design and the `neighbor_colors` reversal are recorded in `../notes.md`.

## Offline canonical-distinction coverage

In the returned ZIP, first extract the native evidence bundle. Two verbose
coverage reports and the historical v1.4.0 census are losslessly compressed as
`.json.gz`; run `python3 checks/restore_evidence.py` from WORK to restore their
exact original paths. The compression manifest binds both compressed and original
bytes. The final `checks/lesson-census-repaired.json` is directly readable.

`canonical_distinction_coverage.py` reads a complete, source-bound shared
`arcpuzzles-lesson-census-v1` JSON report. For every declared rival refuted by
canonical pairs, it requires generated refutation evidence in each explicitly
required band. Canonically fitting rivals' harmless `survived_all` agreement is
reported separately.

`refuted` identifies a candidate demonstration set, not every refuting input.
The exact unique-input count is `null` when the statuses cannot locate witnesses;
the lower bound stays conservative. A single-query `ambiguous` status can identify
the query witness when rotation records are consistent. Coverage is finite and
does not certify semantic approval, identifiability or universal induction.
The helper imports no generator, answer helper or private labels and performs no
Racket replay. Its 35 synthetic tests are under `../tests/test_coverage_tool.py`.

Run from the outer packet folder through the wrapper. This command uses the
retained v1.4.1 census and its exact generator SHA; replace both when checking a
future version. Historical v1.4.0 `final` filenames are not current evidence.

```sh
python3 review.py run python3 generators/9f05dcdedf35/workspace/canonical_distinction_coverage.py \
  ../checks/lesson-census-repaired.json --required-bands easy medium hard \
  --expected-task-id 9f05dcdedf35 \
  --expected-generator-sha256 32eae1598eb032fa4de9d4af7c65aa2113405e9c392b5a8398b2071d5a135ecc \
  --out ../checks/canonical-distinction-coverage-v141.json
```

Payload paths resolve from the packet's `repo`; `../checks/` resolves into `WORK`.
Use a new output name: `--out` refuses overwriting retained reports. Exit 0 means
finite required coverage, 1 means missing distinction, and 2 means incomplete,
errored, malformed or unbound evidence. Actual final evidence is retained in
`checks/coverage-tool/actual-repaired.json`: all 14 canonically refuted namespaced
declarations (seven distinct rivals) have a generated distinction in every band.
The other declarations fit the canonical set and are checked separately by the
lesson ambiguity scorer. The tool reads labels already embedded in the supplied
census; it does not execute a reference or open private solve files.

## Independent semantic probe

`semantic_probe.py` reconstructs components and rival outputs independently of
generator internals. Run `python3 review.py run python3
generators/9f05dcdedf35/workspace/semantic_probe.py --joint --racket --out
../checks/new-semantic-probe.json` from the outer packet folder. `--joint` checks
all 1,008 joint control combinations in four difficulty settings and two roles;
`--racket` obtains actual labels through the public API. Python oracle agreement
is not a replacement for Racket labels. Both helpers are authoring/evidence tools;
keep them closed during visible-only solves.

The optional shared paint-color patch under `WORK/checks/tooling-paint-colors/`
has 15 tests and is not installed. Keep its receipts separate from main-source
checks; it changes checker interpretation, not generator or canonical authority.
