# Baseline rank and preservation witnesses

These are small reproducible witnesses for generator version 2.0.0, source
SHA-256 `08d52d130454fad7f5911f32affa1ed215c3666c2f7e99e2d3d6715e3514e8a4`,
with canonical Racket rule hash `dbb5a0b9e901`. Mathematical minimization was
not performed. They retain the historical baseline behavior; replaying the same
seed against a later generator does not reproduce the baseline input.

Each JSON includes the source/rule binding, exact generation coordinates,
actual input and Racket output, the competing wrong output, and differing cell
coordinates. All coordinates are zero-based. Labels were copied unchanged from
the retained, source-bound Racket execution. JSON extraction and validation do
not constitute a new Racket run.

| Witness | Exact construction | Wrong prediction differs at |
|---|---|---:|
| [First-seen template](baseline_first_seen_template.json) | Baseline `generate(0,0)`, then swap rows 0 and 1 | 3 cells |
| [Frequency template](baseline_frequency_template.json) | Baseline `generate(0,0)`, then swap whole occupied columns 2 and 3 | 6 cells |
| [Nonmodal preservation lesson](baseline_erase_nonmodal_lesson.json) | Seed 0; demonstrations at indices 0, 1, 3, 4; held-out query at index 2 | 6 query cells |

The first two transformed inputs remain in the same `canonical_sparse` profile
and pass the baseline `self_check` and `strict_canonical_like`. The corresponding
fixed-template rivals each matched all 48 sampled unmodified generated inputs
and none of the four canonical pairs. The frequency witness is independent of
the row-order witness: swapping rows leaves column frequencies unchanged.

The preservation rival ranks zeros correctly but collapses all nonzero cells
to the modal nonzero color. It matches all four retained lesson demonstrations,
then erases six color-9 query cells that Racket preserves. The baseline lesson
hook returned no objections. This rival also fits all four canonical pairs.

## Provenance and implementation

- [Original source-bound report](../../../../checks/independent-review/baseline_report.json)
  has SHA-256 `3ed36e79e2819423e0a62fcb5f721357dbb8cfd504fb1ac48835df0f6e9bd3f1`.
- [Original probe](../../../../checks/independent-review/probe.py) contains the
  executable rival definitions and exact sample enumeration.
- [Baseline generator snapshot](../../../../checks/independent-review/baseline_generator.py)
  preserves the source required by the generation coordinates above.
- [Original command receipts](../../../../checks/independent-review/commands.json)
  distinguish baseline findings from later generator checks.
- [Current reusable probe](../workspace/probe_rank_shortcuts.py) checks the
  selected source against declared rivals and independent template/modal
  probes; its scope excludes the shared generic object/position rivals.

The original baseline command was run from the extracted packet root:

```sh
python3 review.py run python3 ../checks/independent-review/probe.py
```

That probe deliberately requires the baseline source hash. The saved input
grids allow independent reference replay after the selected generator changes.

## Replay the saved inputs through canonical Racket

Run these commands from the extracted packet root containing `review.py`.
Choose fresh replay paths if the example output files already exist. The first
command extracts two transformed inputs plus the four demonstrations and query:

```sh
python3 - <<'PY'
import json
from pathlib import Path
folder = Path('WORK/repo/generators/af840d59f24c/counterexamples')
first = json.loads((folder / 'baseline_first_seen_template.json').read_text())
frequency = json.loads((folder / 'baseline_frequency_template.json').read_text())
lesson = json.loads((folder / 'baseline_erase_nonmodal_lesson.json').read_text())
inputs = [first['input'], frequency['input']]
inputs += [pair['input'] for pair in lesson['demos']]
inputs += [lesson['query']['input']]
with Path('WORK/checks/counterexample-replay-inputs.json').open('x') as handle:
    json.dump({'inputs': inputs}, handle)
PY
python3 review.py run python3 -m arcpuzzles apply af840d59f24c \
  --input ../checks/counterexample-replay-inputs.json \
  --check-generator-domain \
  --out ../checks/counterexample-replay-racket.json
```

Compare all seven executed labels with the retained outputs:

```sh
python3 - <<'PY'
import json
from pathlib import Path
folder = Path('WORK/repo/generators/af840d59f24c/counterexamples')
first = json.loads((folder / 'baseline_first_seen_template.json').read_text())
frequency = json.loads((folder / 'baseline_frequency_template.json').read_text())
lesson = json.loads((folder / 'baseline_erase_nonmodal_lesson.json').read_text())
expected = [first['output'], frequency['output']]
expected += [pair['output'] for pair in lesson['demos']]
expected += [lesson['query']['output']]
receipt = json.loads(Path('WORK/checks/counterexample-replay-racket.json').read_text())
assert receipt['executed_rule_hash'] == 'dbb5a0b9e901'
assert [item['output'] for item in receipt['results']] == expected
print('All seven saved labels agree with canonical Racket.')
PY
```
