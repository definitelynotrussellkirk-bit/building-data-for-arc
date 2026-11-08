# aea4d55345a1 carry-policy prototype

**Prototype evidence only.** The canonical generator, selected Racket
authority, approval state, and training admission remain unchanged.

`carry_policy` is fixed for an episode. `skipped_rows` is the exact canonical
program: after shifting the latest diff horizontally, it also advances a prior
row diff when the latest transition skipped that row. `latest_only` omits that
carry action. Every sampled lesson contains one latest-changing row and one or
more skipped rows, so the same inputs are lawful under both settings and the
demonstration labels identify the setting.

The four retained query streams grow from 15×11 to a structurally maximal
27×30 input (four 6-row sections plus three separators). A literal 30×30 input
is incompatible with four equal sections and three separator rows; the 27×30
case stresses the full lawful width and six-row state interaction instead of
padding.

From the packet directory:

```bash
python3 review.py run python3 -m pytest \
  generators/aea4d55345a1/tests/test_parametric_carry_policy.py -q
python3 review.py run python3 \
  generators/aea4d55345a1/workspace/parametric/prototype.py build \
  --seed 17 --demos 3 --queries 4 \
  --out generators/aea4d55345a1/workspace/parametric/evidence/current
```

The atomic writer hashes exact public bytes containing only demonstrations and
query inputs. Private settings, programs, answers, demo-only certificates,
source bindings, and protected-Racket identity are separate. Verification
replays both programs against every pair and rejects inventory, runtime, label,
and identity tampering.
