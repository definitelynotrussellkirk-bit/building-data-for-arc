# Independent code review

## Scope and disposition

Reviewed the selected `2e663d812b7a` generator changes, scalar/large-grid regressions, the size-boundary probe, the separate parametric prototype and its tests, and the optional shared-linter sampling patch. The original selected generator was compared with `.review/baseline/repo/generators/2e663d812b7a/generator.py`. No source files or retained evidence were changed during this review, and no solve contents or private solve labels were used.

**No blocker was found in the selected generator.** One P2 reusable-tool issue was reproduced in the parametric bundle writer: rebuilding into a nonempty directory can carry stale episodes into a new manifest. A separate, nonblocking status-hardening issue was confirmed in the size-boundary probe. **Both findings are now resolved by focused fixes and independently checked below under “Post-fix verification.”** The original findings and their source identities remain recorded for traceability.

## Source identities reviewed

| Source | SHA-256 |
|---|---|
| Selected generator v1.3.0 | `c14518d0be325525090968de13d9598d195cf38a7c5f8732a0d87925cc80ca39` |
| Size-boundary probe before hardening | `31b2e98a62e6452e84c48f838aef1df3322db46214ae5c0e5bc07c1cd1f09a51` |
| Parametric prototype before output-directory fix | `2cc79505ff103aeaf8cae13a27d6783bf1fc417d1fd85ba18ae915a0f2d34ba5` |
| Prototype tests before output-directory regression | `21f6d3ce73c133be5f97390c43d3cd9e538b789b24a7f2da321abfb5c358dd74` |
| Stock shared defect linter | `84eee63069f85e7309d0e8bdc534a72f63aa4bc7abb8f756a3bc66d78381dd7e` |
| Optional proposed defect linter | `43c3883c9b1010aa89333c90195c62bc368130b5085217b3cef8194d6db4975f` |

## P2: a rebuilt prototype bundle can contain stale episodes

**Location:** `repo/generators/2e663d812b7a/workspace/parametric/prototype.py`, pre-fix `build_bundle()`, lines 292–308 and 384–389.

The writer accepts an existing output directory, replaces only the current run's numbered episode files, and then hashes every existing file under that directory into a new manifest. A smaller second run leaves old `public/episode-*.json` and `private/episode-*.json` files in place. The new report does not declare or execute those episodes, yet the new manifest authenticates their file bytes alongside the new report. After a source change, those episodes could also come from earlier source bytes.

The independent prototype reviewer copied the existing two-episode evidence to a temporary directory and performed one actual-Racket rebuild:

```python
shutil.copytree(retained_evidence, out)
report = proto.build_bundle(out, [2026102302])
```

The report returned `status == "pass"`, one episode and seed `2026102302`. Both `episode-0000.json` and stale `episode-0001.json` remained under `public/`. The latter private episode retained seed `2026102301`; both stale files appeared in the newly written manifest. All four stale input hashes were absent from the current run's execution records. The temporary reproduction was removed; the original evidence was not overwritten.

**Required repair:** reject a nonempty output directory before any writes. A focused regression should verify that refusal leaves the existing contents unchanged. Rebuild final evidence in a new directory and preserve the original receipts as pre-fix evidence. This finding concerns safe reuse of the writer; it does not invalidate the original retained bundle described below.

## Nonblocking: size-boundary status omits domain failures

**Location:** `repo/generators/2e663d812b7a/workspace/size_boundary_probe.py`, pre-fix lines 38–46 and 65–83.

The probe records invalid default-sample counts and asks `Catalog.apply` for generator-domain diagnostics, but its `failures` list originally included only model disagreement and override mismatch. `Catalog.apply` deliberately retains the Racket output even when the generator-domain check is invalid, so model equality cannot stand in for the requested domain validation.

A one-off fixture reused the existing 38 actual-Racket outputs and changed only the first result's diagnostic to:

```json
{"generator_domain": {"status": "invalid", "errors": ["injected review fixture"]}}
```

Calling the unmodified probe with that cached application result produced exit code `0`, `status: "passed"`, and `failures: []` while retaining the invalid diagnostic in the report. This is an injected failure-path test, not evidence that the current generator creates an invalid input.

**Recommended hardening:** make nonzero default invalid counts and any reference-domain result other than valid contribute explicit failures. The current retained report has zero invalid default inputs and all reference-domain results valid, so its substantive result remains sound.

## Generator review and targeted checks

The diff adds type/value checks before constructing the generation context. It rejects booleans, floating-point values and strings for seed/index; rejects negative indices; and accepts only `None`, `easy`, `medium`, or `hard` for difficulty. Negative integer seeds remain supported. Exact grid-size and coordinate limits, feasibility checks, and `self_check` dimensions are consistently extended to 30 and coordinate 29. The Racket rule hash remains `f67ec6a58878`.

The schedule is determined by `(seed + sample_index) % 10`: slots 0/2/4 are 16×16, 6/8 are 30×30, 1/3/5/7 have a side over 20, and slot 9 uses sides 9–18. Rich examples remain the five even slots. These are scheduled categories: the random large/small categories can coincidentally produce an anchor shape, so the recipe percentages should not be described as a universal exact histogram of distinct output shapes.

A fresh targeted local check covered seeds −10 through 9, all four difficulty values (`None` and three named bands), and indices 0–9: **800 generated inputs, zero domain or scheduled-category failures**. Each of the **400 rich inputs** distinguished every one of the ten declared rivals against the generator's independent local model. This targeted run did not execute new Racket labels and is not presented as reference-runtime evidence.

Separately, the retained `checks/size-boundary.json` was inspected against the current source hash. It contains **38 reference cases and 38 model matches**, no recorded failures, and the expected executed rule hash. All 15 retained rich examples refute all ten declared rivals. Its three 100-input default populations each have 30 exact 16×16 shapes, 20 exact 30×30 shapes, 60 shapes with a side over 20, and zero invalid inputs.

The retained schedule-census summary binds to the selected generator and records complete fixed-seed coverage of ten starting residues over three bands: 30 lessons and 120 rotations. This is finite fixed-seed coverage. It is not universal identifiability or model-performance evidence.

## Parametric design and current retained evidence

The separate prototype keeps one metric for an entire episode, and input sampling is independent of the selected metric. The default emitted Racket program is byte-identical to the canonical program; the alternative changes only the specified distance expression from `max` to `+`. Public challenge serialization includes demonstration input/output pairs and query inputs, with no parameter, reference program, seed, rival metadata or query answers.

The independent prototype review checked the original `checks/parametric/evidence/` bundle:

- All ten manifest members exist and match their hashes and sizes; there are no extra members.
- All five recorded source hashes match the pre-fix sources and canonical ledger.
- The two emitted program files match their hashes and the exact-text constraints.
- All 24 retained output occurrences—16 episode/metric outputs, two witness outputs, and six boundary outputs—are backed by successful execution records. The report has 47 passing execution records overall.
- Both public challenges exactly match the public projection of their private episode.

The prototype is explicitly separate from canonical generation. Its long-key domain, two-setting scope, finite rival set, and lack of training-admission or model-gain claims remain material limitations.

## Optional shared-linter proposal

An AST comparison of stock and candidate tools found only `lint_one` changed among existing functions; `_sample_requests` and `_sampling_record` are the only added functions. No existing detector or generic-generator function changed.

The proposed fixed seed with consecutive indices avoids the observed `(n, n)` alias for this generator. It also removes cross-seed sampling: a generator whose regime depends on seed alone would receive only seed 1 under the proposal. This tradeoff is disclosed and should remain part of a shared-tool decision. A fixed-seed sweep is finite sampling, not a general guarantee against all legal schedule aliases.

The existing budget provides only indices 0–7 per band for this period-ten generator; the candidate receipt correctly marks coverage incomplete. The retained proposal tests execute the sampling prefix and unchanged axis probe, with separate Racket-backed structural comparison. **They do not establish a full candidate defect-lint or battery pass.** The optional patch remains unselected; stock warnings and the stock battery outcome must remain visible. The separate schedule census and semantic-gate rerun should be reported as their own checks rather than silently replacing the earlier stock battery receipt.

## Limits of this review

This was focused code review plus targeted checks and retained-evidence inspection. It did not rerun the complete regression suite or stock battery, and did not approve training admission. The post-fix checks below cover the two utility findings; they do not expand the stated scope of any other receipt.

## Post-fix verification

**Final review disposition: no remaining blocker found within the reviewed scope.** The P2 nonempty-output issue is resolved. The boundary-probe status-hardening issue is also resolved. The optional linter sampling and finite-evidence limitations above remain applicable.

The independent follow-up is retained as runnable `checks/code-review-postfix.py` and the successful receipt `checks/code-review-postfix.json`. From `WORK`, the exact command was:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python checks/code-review-postfix.py --out checks/code-review-postfix.json
```

The checker exited **0**. Choose a new `--out` filename when rerunning it. It uses temporary directories for the injected probe reports and the copied prototype evidence, preserves the original evidence, and checks source hashes before and after. Its failure-path fixtures reuse retained actual-Racket outputs and do not claim new Racket execution.

### Hardened boundary probe

Current probe SHA-256: `c84da4b3ba2270c1efb4392937e2ca0d5a1a371ab0caa74feb0d629c8e2c7943`.

| Independent fixture | Report status | Probe exit code | Explicit failure |
|---|---|---|---|
| One invalid reference-domain diagnostic; original outputs unchanged | `failed` | 1 | `reference domain check did not validate` |
| One default `self_check` rejection; reference diagnostics unchanged | `failed` | 1 | `default samples rejected by self_check`, easy band, 1/100 invalid |

Both fixtures still had all 38 model/reference output matches, confirming the new failure status comes from the previously ignored domain evidence. The final real-reference report `checks/size-boundary-final.json` is bound to the current probe and unchanged selected generator. Its 38 reference cases have valid outputs and valid domain diagnostics, all 38 model comparisons match, all 300 default samples are valid, and its failure list is empty. Its SHA-256 is `d5be16b3a4a18640b5bd9e9eea323e74bb1767a7ea6f393e661b74648cabe1e9`.

### Prototype output refusal and final evidence

Current prototype SHA-256: `58ed9baf8d56f97fc2c098077bd5ef3e937710421beb85a5b2e67c13b1adfc30`.

The checker copied the final evidence to a temporary nonempty directory and called `build_bundle(out, [2026102302])`. The call raised `FileExistsError`. A sentinel reference-runner constructor confirmed refusal occurred before runtime creation. Every copied file hash and every directory entry remained unchanged. This closes the demonstrated stale-episode path without deleting or rewriting prior evidence.

The final bundle is `checks/parametric/evidence-final/`. Independent validation confirmed:

- All ten manifest members are present, their hashes and byte sizes match, and there are no unmanifested extra files.
- All five source bindings match current files: selected generator, prototype, prototype tests, prototype README, and canonical ledger.
- Both emitted programs match their current materialized program text and recorded hashes; the default remains byte-identical to the canonical program.
- Both public challenges exactly match the private episode's public projection, with only demonstration input/output pairs and query inputs.
- All 24 retained output occurrences are backed by successful program/input/output execution-record tuples. The report contains 47 passing execution records.
- Original retained evidence and selected source files were unchanged by these review checks.

The final manifest SHA-256 is `61d773b2724fd43c57aa7cef42a868e4121a55965a8c9445d55f8550b0b4a3fc`. The current prototype-test hash is `ef00a528cd30cb55187805eb28df439a288813768aacfb2eff8c0d03e653e6b1`; its README hash is `fe6fde55d056100f1f703efe9d8e3c20190b1daf0d7e7b0c29c5486d6dd86caa`. The selected generator remains `c14518d0be325525090968de13d9598d195cf38a7c5f8732a0d87925cc80ca39`.
