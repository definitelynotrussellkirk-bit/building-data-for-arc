## d552baa9e49e

**Finding D552-F1 — A supported lesson start can ask for an undemonstrated command meaning. Status: reproduced; unresolved; findings-only audit.**

Audited generator: `generators/d552baa9e49e/generator.py`, version `2.0.0`, SHA-256 `78b013356c78b80565774363b6dd3eed029b9f825c4a343325f0822c32ccbc5a`. Authoritative canonical rule hash: `21cd1730c540`; rule-text SHA-256: `3ed5fa70e9361bbc394123161fe5fa092ab926161b0cd503b81adea17a39f072`. The current notes are a placeholder and no `evidence/review_index.json` is present for this target.

The generator advertises three demonstrations and schedules commands in aligned four-pair blocks. Its focused lesson test checks only `start = block * 4`. However, the public production API accepts other nonnegative `sample_index` starts. With `Catalog.generate("d552baa9e49e", count=1, seed=0, sample_index=1, difficulty="medium")`, the default three demonstrations and one query are accepted at indices `[1, 2, 3, 4]`, with commands `[2, 3, 1, 4]`. Generation reports no rejections and `lesson_check.status == "not_declared"`.

In that actual produced lesson, neither command 4 nor command 5 appears in a demonstration. A concrete rival that exchanges their meanings—command 4 reflects up/down and command 5 reflects left/right—matches all three authoritative demonstration outputs exactly and changes the query answer. This is a failure to determine the query from the demonstrated command meanings. All individual inputs pass `self_check`; correct individual labels do not detect this lesson-level gap.

The query input SHA-256 is `ae14c51de70207b51b92b6587e27ccf8be8260c8eb30cdcab6212ae1a1a04ce6`. Its canonical output is `[[0,8,6],[0,6,8],[6,0,8]]`; the rival gives `[[8,0,6],[8,6,0],[6,8,0]]`. Their output hashes are respectively `8e8310a72e812af3194f4abb13752449bfa4420e1975a87b9eeec76f04af3f35` and `9c5c45950aca3d3a70145832d644976b140c14064e8756265142b11ab9f6d963`.

A bounded census generated seed-0 inputs at indices 0..22 separately for easy, medium, and hard, then checked each four-pair window starting at 0..19. **13/20 windows in each band, 39/60 overall, admitted a command-swap rival that fits every demonstration and changes the query.** The script retained each window, exact command swap, input hashes, and authoritative outputs. Its independent transform table matched all five stored canonical labels. `Catalog.apply` supplied authoritative outputs for all 69 generated inputs, and the independent table matched all of them. These are finite measurements, not an all-seed claim.

**Reproduction command**, run from the outer packet root:

```bash
python3 review.py run ../.venv-review/bin/python ../checks/audit/d552baa9e49e/reproduce.py
```

The wrapper executes the payload from `WORK/repo`. Exit code: **0**; measured elapsed time: **10.896 seconds**. A zero exit here means that the reproducer successfully asserted and recorded the defect. Exact command, working directories, stdout, stderr, and reproducer hash are in `checks/audit/d552baa9e49e/command.json`.

**Evidence:** `checks/audit/d552baa9e49e/reproduce.py`, `checks/audit/d552baa9e49e/report.json`, and `checks/audit/d552baa9e49e/command.json`. The report contains the full public production episode, its source/rule provenance, all census recipes, and the independent rival outputs.

**Scope and limits:** Starts divisible by four repeat a demonstrated query command; this finding concerns other supported starts. No full battery was run, and no audited source, tests, notes, reference rule, or approval record was modified. A repair should ensure that each materialized query's command meaning is demonstrated, or reject/rebuild lessons that fail that check, and exercise starts beyond aligned blocks.
