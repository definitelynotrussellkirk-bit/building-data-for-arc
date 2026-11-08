# Public a25697e4: fit a key, then use its reflection parity

This is a new, unapproved public-evaluation family. `reference.rkt` in the task
root is a general geometric program; it contains no supplied-grid or answer
lookup. The immutable `workspace/public-parent.json` identifies the original
parent. Owner registration, source review, native qualification and acceptance
remain separate from the authoring preflight.

## Original rule and parameter

Infer the unique modal background. Same-color four-connected components that
contact a canvas edge form anchored socket fragments. Group fragments by their
edge and color, so disconnected fragments of one socket stay together and
same-colored sockets on different edges stay separate. The tight rectangle of
each socket has a nonempty background cutout. Remove these anchors when finding
the remaining colorblind four-connected pieces; each piece has two colors.

Find a one-to-one assignment of pieces to sockets. One complete color region
must exactly match the socket's cutout under a D4 rotation/reflection and a
translation. Check the entire transformed piece against canvas bounds and all
stationary anchors. Clear all free pieces simultaneously; their old positions
do not block destinations. Final moved pieces must not overlap. The admitted
grammar requires exactly one complete placement assignment.

The private episode parameter is `reflection_colors`:

| Setting | Color behavior after geometric placement |
|---|---|
| `swap` (default) | Exchange a key's two colors exactly when its fitted D4 transform is a reflection. |
| `preserve` | Preserve both colors for every fitted transform. |

The adjacent `canonical.rkt` and default `program` string equal root
`reference.rkt` byte-for-byte, keeping the authority inside the native resource
closure as well as the public authoring closure. Both
settings preserve the original socket identification, shape fitting, whole-key
collision rejection and simultaneous movement. In the default, the geometric
fit supplies an input-derived reflection parity that controls the later color
assignment. A witness can replace only those selected parity bits, holding
destination cells and painting code fixed, and change the final answer.

## Supported domain

Grids are rectangular built-in lists of built-in lists, each axis in 1..30,
with exact integer colors 0..9 and a unique modal background. One to four
sockets are allowed. Anchored components cannot contact multiple edges;
one socket is represented for each `(edge, color)`. Each socket rectangle
contains only its own anchor color and background. Every free piece has exactly
two colors. Unmatched pieces, solid sockets, ambiguous assignments and malformed
grids are rejected. All five supplied labeled examples, including both test
gold outputs, belong to this grammar. Generated scenes use one or two sockets;
the larger validator domain is not an exhaustive generated distribution.

`plan(grid)` exposes selected socket/key indices, D4 matrix index and parity,
head color, the two original colors, translated cells and translation.
`solve(grid, reflection_colors="swap")` is a Python diagnostic mirror; protected
Racket remains the executed label check. No helper imports a predecessor packet.

## Episodes and construction

`generate(seed, settings=None, demos=3, queries=4)` accepts exact integer seeds
0..2**63-1, independently requested demos 2..6 and queries 1..4. The ordinary
default is three demos; the tested supported minimum is two. Settings are fixed
for the whole episode. Separate SHA-derived RNG streams select the setting,
demonstration augmentations and query augmentations. Equal seeds/counts have
equal inputs under both settings.

Two rich teaching cores each contain one rotational and one reflected fit.
They cover same-colored sockets on different edges, shared piece/socket colors,
equal-area but different-shaped key parts, symmetric heads requiring attached
tail collision checks, and nearest-socket assignment foils. Their constructors
were copied explicitly from this packet's independently checked design, with
provenance retained under `checks/public_eval_a25697e4/`.

A protected counterexample caught a numeric-color shortcut in the initial
second core. Its two keys now use opposite head/tail color roles, so one head
is numerically lower and one higher under every palette permutation. Together
with the first core's shared colors and mixed reflection parity, this teaches
geometry-dependent coloring in both settings. The original failing scene and
its executed rival prediction are retained separately.

All scenes use a seeded bijective palette permutation and a whole-canvas D4
transform. This preserves fitted reflection parity. The full six-demo/four-query
bank is constructed before either count is sliced, and the complete query bank
is shuffled before a shorter query prefix is selected. The controller's export
applies a separate private presentation shuffle. Inputs are fresh and distinct
within an episode; query answers never become demonstrations.

Base dimensions are 20x24 and 26x22 for the cores; 10x14, 14x18, 26x28 and
30x30 for extra demos; and 12x17, 16x21, 24x28 and 30x30 for the four queries.
Quarter-turn augmentation can exchange height and width. The 30x30 demo and
query contain 195 and 235 foreground cells respectively, including 66 and 75
free-key cells. Socket, head and tail sizes grow together. Construction uses
fixed valid placements with no fallback or rejection loop.

The root `generator.py` returns individual canonical inputs using the keyed
generator context and the same constructors. It declares no exact override
axes. The native adapter, rather than arbitrary subsets of individual draws,
owns the tested complete teaching/query assembly.

## Run from the packet outer directory

```sh
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 -m pytest generators/public_eval_a25697e4/tests -q
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 generators/public_eval_a25697e4/workspace/parametric/audit_native.py --out ../checks/public_eval_a25697e4/teaching-new
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_a25697e4 --root . --out ../checks/public_eval_a25697e4/preflight-new
```

Use new output paths. The finite audit fits plausible rivals using only the
supported demo prefix, freezes its survivors, then scores each against all four
queries. It also executes every official training and provided test-gold label.
Authoring preflight and causal/export receipts grant no owner acceptance or
training admission. Programs, settings, seeds, answers, placements and future
query inputs remain private to the controller.
