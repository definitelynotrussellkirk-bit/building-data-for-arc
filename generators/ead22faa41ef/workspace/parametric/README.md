# Survivor-role parameter prototype

This task-local, opt-in prototype adds one episode-level rule parameter without
changing the production generator's canonical default:

- `green3` (default): paired 3 becomes 8 and paired 2 becomes 0.
- `red2`: paired 2 becomes 8 and paired 3 becomes 0.

Inputs are generated independently of the hidden setting. Every demonstration
and query contains an isolated 3/2 pair plus at least one preserved lone 3 and
lone 2. That makes the alternate setting and the historical global replacement
shortcut testable from the demonstrations. Labels are produced by the matching
exact Racket program, not by the Python mirror.

Create fresh bounded evidence from the packet root:

```bash
python3 review.py run python3 generators/ead22faa41ef/workspace/parametric/prototype.py \
  materialize --seed 20 --demo-count 3 --query-count 4 \
  --out ../checks/parametric/survivor-role
```

Replay every retained rule, label, rival analysis, public projection, content
ID, and file receipt:

```bash
python3 review.py run python3 generators/ead22faa41ef/workspace/parametric/prototype.py \
  verify --out ../checks/parametric/survivor-role
```

The evidence is deliberately bounded. It is not a canonical-rule change,
shared runtime/catalog integration, approval, or training admission.
