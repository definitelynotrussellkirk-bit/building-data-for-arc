## 3e68f3e3f66f

**Finding: independently reproduced unresolved production lesson-level shortcut. Audited source unchanged.** Generator SHA-256: `b250f517e5ab3c165640f00fc87e04e593ff3cd58098ec9da4f842ca33ff58f8`; selected/executed rule hash: `4f92f2063a9e` (match).

The rival copies only the first three row-major eligible motif cells, retaining the intended legend, first source, row-major destination ordering, translation, recoloring, clipping, and copy overwrite behavior. It fits **5/5 labelled canonical pairs**, whose motifs each contain exactly three eligible cells.

A bounded fresh probe reproduced this default medium lesson at seed `13`, with no profile overrides:

| Role | Sample index | Emitted profile | Rival matches Racket |
|---|---:|---|---|
| Demo | 0 | `clipped_copy` | Yes |
| Demo | 1 | `single_broadcast` | Yes |
| Demo | 2 | `legend_colored_motif` | Yes |
| Query | 3 | `sparse_wide_motif` | **No** |

All four emitted inputs pass `self_check`; their Python-mirror outputs match fresh selected-rule Racket execution. On query cell `(9,17)`, zero-indexed, Racket paints `9` from the fourth motif cell; the rival leaves `0`. Thus the demonstrations do not refute this canonical-fitting rival before it changes the query. This is a production sampling finding, not a validator-only mutation. The generator independently samples profiles and declares no `lesson_identifiable` hook. The finding independently confirms the two same-source unresolved audit records already in the current review index; it is not claimed as a new distinct defect.

Evidence:

- `checks/audit/3e68f3e3f66f/finding.json`: source/rule hashes, seed, difficulty, indices, canonical counts, per-input hashes, rival outputs, exact differing cells, commands, cwd and exit codes.
- `checks/audit/3e68f3e3f66f/input.json`: four exact generated inputs.
- `checks/audit/3e68f3e3f66f/racket.json`: fresh supported selected-rule apply receipt with all four oracle outputs.
- `checks/audit/3e68f3e3f66f/probe.py`: executable bounded reproduction.
- `checks/audit/3e68f3e3f66f/apply.log`: wrapper/apply execution log.

From cwd `/workspace/scratch/944df838b1d1/packet/WORK/repo`, the probe command `/workspace/scratch/944df838b1d1/packet/WORK/.venv/bin/python ../checks/audit/3e68f3e3f66f/probe.py` exited **0**. The probe invokes the supported `run_with_racket.py` wrapper with the absolute environment Python and `python -m arcpuzzles apply`; that command also exited **0**. It confirmed source bytes unchanged afterward. This audit ran four generated pairs and five canonical comparisons, not a full battery or prevalence census.

**Suggested repair:** register the first-three-cells rival and ensure every demonstration set contains sufficient four-cell motif evidence, including redundancy if arbitrary query rotation is required. Mere global availability of the `sparse_wide_motif` profile does not provide that guarantee.
