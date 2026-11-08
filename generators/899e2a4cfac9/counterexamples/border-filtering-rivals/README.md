# Exact semantic counterexamples

These four small 7x8 grids were handmade during the initial diagnosis of generator 1.2.0. The unchanged canonical Racket rule independently labeled them. `input.json` contains the four inputs in order; `expected.json` records the explicit authoritative outputs in the same order; `reference.json` retains the original public-application receipt. `provenance.json` retains original/final generator hashes, the executed rule hash, input/output hashes, named rival outputs, original command/cwd/exit status, and the final source's actual validator verdicts.

| Index | Name | Disagreement |
|---|---|---|
| 0 | `size_role_swap` | Border L disappears while interior domino survives; refutes erase-domino, size-threshold, and global-largest filtering |
| 1 | `same_color_diagonal_contact` | Diagonal same-color contact does not join an interior component to a border component; refutes same-color eight-connectivity and global border-color deletion |
| 2 | `different_color_edge_contact` | Orthogonal different-color contact does not join an interior component to a border component; refutes all-nonzero four-connectivity |
| 3 | `same_color_disconnected_roles` | A disconnected interior component survives even when its color also appears on the border; refutes global border-color deletion |

All four inputs pass the final source's broad `self_check`; each has two border components and two interior components. These exact grids are diagnostic witnesses, not a claim that the default stochastic generator emits their precise pixels. Inputs 0 and 2 contain four components and five colors including zero, beyond the current four-component constructor's color-role palette limit. Axis compatibility for the other two inputs is also not a positive exact-emission proof. The current default rich draws construct equivalent distinguishing relationships with seven components and additional witnesses.

Original source SHA256: `3f5dc2b5704c96aaf9ac3bb33dc6e8c75c1772692fcb431b63a397f139edcf0e`. Documentation/current-validator source SHA256: `0fe1fd03f31b285873c464d28ad3e0356299f3f6709fb75c1af57c5dd68a7ce5`. Executed canonical rule hash: `50ed982b7d21`; rule-text SHA256: `e3be5a37984b21bbb87a5d1347a612058e29f5c34c30306dbe716914a789fcc3`. The receipt's generator hash intentionally describes the original execution, while the documentation-validation hash describes the final source; neither supersedes the other.

Reproduce through the public application command. From the review packet's `WORK` directory:

```bash
python3 run_with_racket.py python3 -m arcpuzzles apply 899e2a4cfac9 \
  --input generators/899e2a4cfac9/counterexamples/border-filtering-rivals/input.json \
  --out generators/899e2a4cfac9/counterexamples/border-filtering-rivals/replayed-reference.json
```

In an installed standalone checkout, run the same `python3 -m arcpuzzles apply` payload from the repository root. Compare each result's `output` with the corresponding `expected.json` entry, and require the executed rule hash to match `50ed982b7d21`. The original successful command is retained verbatim in `provenance.json`; the command above is a relocation-friendly reproduction recipe, not a claim that an additional execution was run during documentation finalization. No private solve data is included.
