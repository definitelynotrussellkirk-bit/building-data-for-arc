# Proposed frequency-extreme prototype

**Status: proposed, unapproved, separate from canonical generator repair.**

This runnable task-local extension keeps the original object reasoning and
changes one episode-fixed enum, `frequency_extreme ∈ {minimum, maximum}`.
The canonical/default setting is **minimum**. The maximum setting selects a
component whose color occurs most often across the entire grid. Neither setting
ranks individual component sizes. Both enumerate monochromatic nonzero
four-connected components in row-major order, preserve the first component on a
global-count tie, and crop the original input to that component's bounding box.
The crop retains zeros and other colors within the box.

## Interface

```python
emit_rule(frequency_extreme="minimum")       # complete exact (rule! ...) text
choose_setting(seed)                         # deterministic episode-level choice
make_input(seed, pair_index)                  # independent of hidden setting
generate_episode(seed, frequency_extreme=None, n_train=3, n_test=1)
# -> {"public": {"train": [...], "test": [{"input": ...}]}, "private": {...}}
```

An omitted `generate_episode` setting is chosen once from its seed; an explicit
setting remains fixed for every demonstration and query. An omitted `emit_rule`
setting is the original minimum. The minimum rule matches the canonical record
byte for byte. Maximum wraps only its global-frequency sort key in unary minus,
so ascending stable sorting implements descending frequency without reversing
stable ties. No production generator, runtime, canonical record, or approval
metadata is changed.

`generate_episode` executes demonstrations first, executes both declared
parameter rivals against **only those demonstrations**, and requires exactly
one consistent setting before constructing/executing the query. Labels always
come from actual `RacketBridge` execution and are cross-checked against a Python
debug mirror. `rule!` is a controller registration form rather than a Racket
prelude function; the runner removes precisely the outer `(rule! ...)` wrapper
and applies its unchanged lambda, as the repository controller does. It retains
the exact emitted program, callable hash and executed output receipts.

## Bounded input domain and constructor

Both settings use rectangular 5–30 by 5–30 grids of literal integer ARC
colors 0–9 with at least two nonzero colors. Each setting additionally requires
its own selected component bounding box to be smaller than the full grid.
Consequently, their accepted arbitrary-grid domains can differ: a 5×5 grid of
color 2 with a single central color 3 is accepted for minimum and rejected for
maximum. The episode constructor checks both settings and uses their shared
support. Global-frequency ties are supported.
The constructor is independent of `generator.py` and uses its own local seed
stream. Its three nonzero colors have global counts 9, 13 and 18. Each color has
separate components, and hollow/open shapes retain background or an intruding
color in crops. Colors and orientation vary with pair seeds. Minimum and maximum
produce different outputs on every constructed pair. The first demonstration
contains rich crops; later orientations can change which disconnected component
is encountered first.

The constructor is deliberately compact. It demonstrates the changed rule and
its identifiability, and does not establish broad generation diversity or
production suitability. Only the two declared parameter settings are tested as
rivals. There is no claim that every plausible unrelated shortcut is excluded.

## Run from a full review packet

The packet needs Python 3.12+ and its included offline Racket. These commands
execute from the outer directory containing `review.py`; payload paths are
relative to `WORK/repo`. `python3` may be replaced by the packet's prepared
`WORK/.venv/bin/python` absolute path when running tests.

```bash
python3 review.py run python3 \
  generators/7944933e200f/workspace/parametric/prototype.py \
  --out ../checks/parametric/frequency-extreme-v1

python3 review.py run python3 -m pytest -q \
  generators/7944933e200f/tests/test_parametric_prototype.py
```

The evidence directory must be new or empty. The alternative equivalent launcher
from `WORK/` is `python3 run_with_racket.py python3 ...`. In a complete independent
repository, install Racket on `PATH` or set `RACKET_PATH`, then run
`python3 generators/7944933e200f/workspace/parametric/prototype.py --out var/prototype`
from the repo root. No predecessor source, sibling checkout or generator module
is imported. The runner inserts only its own repository's `shared/runtime` path.

## Retained evidence

The CLI writes only two challenge files under `public/`, named by index. They
contain demonstration inputs/outputs and query inputs; they omit hidden
parameters, seeds, rules, hashes and query answers. Keep the entire `private/`
directory from a solver. Private files contain the two complete episodes with
query labels, exact per-setting Racket programs, source/program/input/output
hashes, a shared lawful input with differing executed outputs, four literal
semantic witnesses, execution receipts and a manifest. The `.rkt` display files
end with a newline; program hashes use the exact UTF-8 bytes returned by
`emit_rule`, without that added newline.

The finite CLI probe executes **30** transformations: 10 per episode (3 chosen
rule demos, 6 rival-demo checks, 1 query), 2 settings on the shared differentiating
input, and 2 settings on each of 4 semantic witnesses. The focused test file is
prototype-only coverage and separately exercises both complete settings,
determinism, visibility boundaries, canonical text identity, invalid values and
literal semantic regressions. The evidence manifest and test log report actual
run counts. A canonical-only staged Python mirror first failed the maximum
fragmentation assertion, before adding the maximum selector; that failure is
retained in `checks/parametric/canonical-only-red.log`.

Successful prototype tests do not approve a rule variant, update canonical
safety, or add a production episode-rule API. Those remain separate decisions.
