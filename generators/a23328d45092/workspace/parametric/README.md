# Native parametric family: a23328d45092

`postprocess=canonical` returns the selected canonical program byte-for-byte.

`postprocess=highlight_visible_majority` is a sequential composition:

1. Apply the canonical zero-transparent `TL > TR > BL > BR` overlay.
2. In that visible overlay, choose the most frequent nonzero color (lowest
   color wins a tie) and recolor all of its visible cells to 9.

The generated scenes reserve 9 for the second stage. Their BR source patch is
large enough to be the raw-source majority, while occlusion makes another
color the visible majority. `counterfactual_program()` intentionally chooses
before overlaying and is retained for the causal witness.

The adapter supports 2–6 demonstrations and 1–4 private queries. Qualification
uses three demonstrations, and the fourth query is a substantive 30×30 input.

## Re-run the bounded audits

```bash
python generators/a23328d45092/workspace/parametric/audit_native.py \
  --seeds 256 \
  --out generators/a23328d45092/workspace/parametric/evidence/current-native/native-audit.json
python generators/a23328d45092/workspace/parametric/audit_base_teaching.py \
  --seeds 256 \
  --out generators/a23328d45092/workspace/parametric/evidence/current-native/base-teaching-audit.json
```

The first checks the native episode/export contract and wrong-order causal
counterfactual. The second checks every consecutive three-example base lesson
against all noncanonical quadrant priority orders, plus 5×5 and 30×30 bounds.
Both are bounded evidence rather than universal uniqueness proofs.
