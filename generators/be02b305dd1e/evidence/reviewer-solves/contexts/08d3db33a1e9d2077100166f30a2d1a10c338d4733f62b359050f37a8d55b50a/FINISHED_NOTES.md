# Solve work log

## Exposure declaration

I had already inspected the assigned generator and rule before this required post-repair solve, so earlier rule exposure is **yes**. During this solve I kept the generator, Racket rule, reference solutions, private query labels, and prior solution explanations closed and used only `solve/challenge.json`, the visible examples, and my own Python checks.

## Revision 1 — relative mask transfer

Visible examples show one solid green component and one or two magenta components. The green region is removed. The largest magenta component is preserved, and its occupied cells relative to its own bounding box are redrawn in cyan at the green component's bounding-box origin. A smaller magenta component, when present, is unchanged and is not used as the stencil.

I implemented four-connected color components, selected the largest magenta component, matched the unique green component with the same bounding-box dimensions, cleared that target, and stamped the magenta relative coordinates as color 8. I retained explicit shape/target checks rather than assuming fixed grid dimensions or a fixed object position.

Local visible-only validation command:

```sh
cd WORK
python3 - <<'PY'
import importlib.util, json
spec = importlib.util.spec_from_file_location('episode_solution', 'solve/solution.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
challenge = json.load(open('solve/challenge.json'))
for index, pair in enumerate(challenge['train']):
    assert module.solve(pair['input']) == pair['output'], index
print('all visible training examples matched')
PY
```

Remaining uncertainty before the episode checker: the visible set makes the largest-component choice and bounding-box-relative orientation clear, but private query correctness remains intentionally hidden.
