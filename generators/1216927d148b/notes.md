# Working notes: 1216927d148b

## Review `review-60f652c3e40fcdc9`

The production generator and canonical Racket authority remain unchanged. The
new native parametric family lives in `workspace/parametric/` and varies one
rule axis, `gallery_order`:

- `fixed_pairs` is the exact canonical AB, AC, BC gallery and returns the
  canonical program byte-for-byte.
- `largest_overlap_first` derives the same three pairwise intersections, counts
  their occupied cells, stably orders them by decreasing count (AB before AC
  before BC on ties), and concatenates them in that input-dependent order.

Inputs are matched across settings. Episodes support independent 2–6
illustrations and 1–4 queries; prefixes are stable, four queries are distinct,
and the last query is a substantive 30×17 case touching all four boundaries.
The canonical grammar has three fixed five-column panels plus two separator
columns, so an exact 30×30 input would require ignored columns or a visible
change of grammar and was deliberately not fabricated.

The first two demonstrations constructively teach both rank ordering and stable
tie-breaking. A protected-Racket audit tested nine executable shortcuts against
both settings using the minimum two demonstrations and four queries: all nine
were rejected (50 evaluations). Native qualification passed two settings at
seeds 0 and 17 (four jobs, 32 protected-Racket evaluations).

Sequential dependency: step A computes the AB/AC/BC masks and their counts; the
intermediate is the source-ordered `(pair, mask, count)` list; step B sorts that
list and lays out the final gallery. The retained qualified witness has counts
3/5/4, so the selected order is AC/BC/AB. Replacing the intermediate with the
fixed AB/AC/BC order changes the final protected-Racket output.

The complete portable task suite initially exposed an inherited test-only path
bug: two tests looked for canonical data beneath a fixed parent depth. They now
use `reviewer_support.find_root` and `canonical_path`; 42/42 isolated task tests
pass. This did not change the production generator or native program bytes.

Evidence:

- `WORK/checks/1216927d148b/self-audit/report.json`
- `WORK/checks/1216927d148b/qualification/qualification.json`
- `WORK/checks/1216927d148b/qualification/execution.json`
- `WORK/checks/1216927d148b/causal/witness.json`
- `WORK/checks/1216927d148b/causal/replay.json`
- `WORK/checks/1216927d148b-tests/result.json`

Status is reviewer-ready only. Owner exact-source integration, fresh native
qualification, acceptance, and any training admission remain pending.
