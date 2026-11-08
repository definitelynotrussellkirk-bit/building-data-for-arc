# Logical compression and component crop

This separate family for `c1fd38e5812b` exposes the episode-fixed parameter
`view=compressed|largest_component_crop`. The default returns the exact Catalog
Racket source in `canonical.rkt`. Production generation and its calibrated
sampling distribution are unchanged. The inherited module rule pin is not used
as the execution authority; the selected Catalog rule is `0805714fcf25`.

## Rule and dependency

First compress consecutive duplicate whole rows and then consecutive duplicate
whole columns. Nonconsecutive repetitions remain. This is the actual canonical
`compress-grid` behavior. On this family's exact Cartesian expansions, detecting
the visible first-column/first-row run boundaries produces the same logical grid.

`compressed` returns that grid. `largest_component_crop` discovers every
four-connected monochrome component of the logical grid, including color zero,
and chooses greatest occupied logical-cell count. Ties use ascending bounding
box `(row1,col1,row2,col2)`, then ascending color. Return the corresponding
rectangle from the original compressed grid, preserving every interior color;
do not isolate the component or fill its rectangle with a solid color.

The intermediate changes the selection. Expansion assigns different physical
areas to different logical cells, so a component that appears larger in input
pixels can lose after compression. One core teaching case has two six-cell
logical components: bbox order chooses one, while physical area chooses the
other. The selection and crop therefore depend on the recovered logical state.
This is a derived-grid dependency, not iterative physical simulation.

## Grammar and coverage

Inputs are exact Cartesian expansions of logical grids with dimensions 2..10
on each axis. Logical grids use at least four colors from 0..9. Every run span
is 2..12 and each expanded dimension is at most 30. Adjacent logical values on
the first row and first column differ, making every run boundary observable.
Interior neighbors and nonconsecutive whole logical rows/columns may repeat.
The separate prototype grammar reaches 4x4 through 30x30; the unchanged
production validator remains calibrated to 8..24 and logical dimensions 2..6.

Every request constructs a complete six-demo/four-query bank, independent of
setting and requested prefix lengths. Both settings share all input grids.
Changing demo/query counts preserves prefixes, and all ten complete-bank inputs
are distinct. Seeds are exact integers in 0..2**63-1; booleans, floats, unknown
settings and unsupported counts are rejected.

Three core demonstrations teach complementary roles:

1. A zero-colored ring wins, with preserved interior color and nonconsecutive
   repeated logical rows/columns. Row spans are nonuniform, column spans uniform.
2. Two components tie in logical area while their expanded physical areas differ.
   Bbox order chooses the lower-color component. Row spans are uniform and column
   spans nonuniform, or both axes swap consistently for the whole lesson. A
   smaller earlier component prevents selecting the first nonsingleton object.
3. A component-area tie separates occupied-cell count from bounding-box area,
   with bbox order now choosing the higher-color component.

The opposite tie-color orderings repair a concrete earlier three-demo seed-zero
lesson: a minimum-color-only tie rule fitted all demonstrations but failed a
query, returning `[[1]]` instead of `[[5]]`. The exact previous source, native
programs and replay are retained under `checks/c1fd38e5812b/tie-color-before/` in
the reviewer delta. The repair keeps the three-demo minimum.

A second retained seed-zero failure selected the first nonsingleton component:
all three demonstrations fitted, but query2 selected seven logical cells instead
of eleven. Adding the earlier two-cell component closes that demonstrated hole
without changing the three teaching roles. Protected before-repair evidence is
in `checks/c1fd38e5812b/first-nontrivial-before/`.

Ring dimensions, target topology, palette, axis orientation, run lengths and
additional random connected shapes vary across seeds. The first query is the
literal 4x4 minimum at seed zero, with small varied logical scenes and occasional
minimum cases elsewhere. Later queries include large rectangular scenes and a
30x30 expansion of a 10x10 logical grid. The dense case has 100 logical cells
with components distributed through the canvas; zero remains an ordinary color.
The sampler report records actual diversity and retries rather than asserting
universal coverage.

Teaching selection, extra-example novelty and query novelty each have explicit
128-attempt limits. The constructive Python screen checks 19 named natural
rivals. Its independent protected Racket audit is `audit_native.py`; equivalent
selection interpretations are allowed under the default compressed setting.
Finite teaching checks do not prove universal identifiability.

## API and execution

`adapter.py` loads the adjacent implementation by exact path and exposes:

```python
program({"view": "compressed"})
generate(seed, {"view": "largest_component_crop"}, demos=3, queries=4)
```

The supported range is 3..6 demonstrations and 1..4 queries, with defaults 3/4.
`prototype.py` additionally supplies `compress`, `expand`, `analyze`,
`validate_grid`, `components`, `bbox`, `select_component`, `crop`, and `solve`.
Returned Python labels are claims until the native worker independently executes
the Racket program. The program's base31 bbox key is an exact encoding of the
declared lexicographic order for coordinates within 30x30; component size always
dominates that key.

`make_examples.py` executes both settings through the protected worker before
calling `export.py`. Controller files retain four query inputs; each actor turn
contains only the demonstrations and one current masked query. Settings,
programs, future queries, private outputs and source certificates remain
controller-private. Give the actor one `turns/<id>.json`, never the bundle index.

From the outer packet directory, using fresh output destinations:

```sh
WORK/.venv/bin/python review.py run --receipt checks/c1fd38e5812b/family-tests-command.json python3 -m pytest generators/c1fd38e5812b/tests/test_parametric_c1fd38e5812b.py -q
WORK/.venv/bin/python review.py run --receipt checks/c1fd38e5812b/audit-command.json python3 generators/c1fd38e5812b/workspace/parametric/audit_native.py --out ../checks/c1fd38e5812b/audit
WORK/.venv/bin/python review.py run --receipt checks/c1fd38e5812b/examples-command.json python3 generators/c1fd38e5812b/workspace/parametric/make_examples.py --out ../checks/c1fd38e5812b/examples --seed 0 --demos 3 --queries 4
```

After the source/evidence inventory is current, use native qualification:

```sh
WORK/.venv/bin/python review.py run --receipt checks/c1fd38e5812b/qualification-command.json python3 -m arcpuzzles parametric qualify c1fd38e5812b --seed 0 --seed 17 --seed 101 --demos 3 --queries 4 --out ../checks/c1fd38e5812b/qualification --summary
```

Focused tests, source inventory, qualification and causal replay remain reviewer
evidence. Exact-source owner acceptance is pending, and training admission is a
separate decision. Inherited production findings are not cleared by this family.
