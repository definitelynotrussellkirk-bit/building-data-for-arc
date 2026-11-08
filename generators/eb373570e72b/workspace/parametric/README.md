# Ranked barriers: native parametric candidate

`blocker_rank=1` returns the exact canonical Racket source. `blocker_rank=2`
selects the second **vertical marker column** to the right of each loose blue
cell. With fewer than the requested number of barriers, the run has length
three, clipped to the right boundary. Painting happens after chain placement,
so a rank-two run can overwrite the bottom of a skipped vertical column.

The dependent steps are active-row discovery → three-spaced chain
classification → ordered vertical columns → ranked endpoint → floor painting
and red-gap closure. A red member of a blue-containing chain is not a barrier.
The nonstaggered red-to-blue handoff and conditional gap closure remain intact.

## Supported grammar and counts

- Demonstrations: **2–6**, default **3**. Queries: **1–4**, default **4**.
- Inputs and their ordering are independent of the setting and requested
  counts. Every requested input is distinct within its episode. Seeds are
  exact integers from 0 through `2**63 - 1`; booleans are rejected.
- Active marker columns remain monochromatic suffixes. Nonstaggered columns
  occupy the full height. The prototype additionally permits loose blue
  fragments on disjoint lower rows, with at most one extra blue cell per row.
  Thus M active markers and lower counts of at most M+1 preserve the intended
  first near-busiest row. This is a separate sampler extension; the canonical
  generator and its 3–9-row envelope remain unchanged.
- Four queries include 3×7, a varied staggered scene, a substantive 30×30
  scene with ten marker columns and two loose regions, and a suffix-only
  scene. The large input uses both horizontal edges and all thirty rows.
- The first two demos constructively show both scene modes, individual-column
  ranking, insufficient-barrier fallback, clipping, earlier red evidence,
  blue overwrite, and conditional red-gap closure. Additional demos vary the
  scene. No retries or silent short batches are used.

## Run from the outer review packet

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/eb373570e72b/workspace/parametric/prototype.py \
  --seed 17 --demos 3 --queries 4 --out ../checks/ranked-barriers-new
```

Omit `--rank` to generate one episode per setting on matched inputs. Supply
`--rank 1` or `--rank 2` for one setting. Every label is executed through a
protected Racket process. `adapter.py` loads this implementation by exact path
and supplies `program(settings)` and `generate(seed, settings, demos, queries)`
to the existing native qualification/export API.

The CLI also executes the task-local finite rival audit. A rival must fit all
visible demonstrations before its query disagreement is considered. The
retained regression shows why the earlier two-column teaching anchor was
insufficient: paint hid endpoint differences. Three vertical columns now
separate the endpoint witness from the shortage witness without adding a demo.
This is bounded evidence against the declared rivals, not universal uniqueness.

## Public data and sequential use

`public/<sha256>.json` contains only demonstrations and query inputs, with IDs
computed from the exact visible bytes. `private.jsonl` retains settings,
programs, all answers and Racket identity. The four-query public file is a
**controller container**. Use `prototype.visible_query(episode, index)` to
project one query without future inputs, answers, total counts or turn hints.
First-turn bytes are identical for one-query and four-query generation.

`write_export` is a serializer for already generated episodes, not an admission
gate. It refuses duplicate visible payloads and existing destinations. Use the
existing native accepted-family export after owner acceptance for production.

## Qualification and limits

Focused tests are in `../../tests/test_parameters.py`; the inherited task test
now resolves canonical data through the portable reviewer helper. The native
inventory is `evidence/manifest.json`; the reviewer qualification and causal
witness are returned under `WORK/checks/eb373570e72b/`.

The candidate preserves the production source and canonical authority. It does
not resolve the inherited canonical sampling/profile and missing production
lesson-contract audit. Native qualification is a reviewer result; the owner
must qualify and accept the exact integrated source. No training admission or
mixture change is made.
