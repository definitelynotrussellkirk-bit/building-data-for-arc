# Native parametric family: `c286f4a2923f`

`finish=transfer_only` is the selected canonical Racket source byte-for-byte.
`finish=fill_transferred_holes` first transfers the color-2 source mask to the
color-3 target's top-left anchor in cyan, then fills every background pocket
enclosed by that transferred mask with yellow.

The settings use identical inputs. Three demonstrations include a no-hole mask,
a one-hole ring, and a two-chamber mask. Four queries include boundary contact,
multiple topology changes, and a substantive 30×30 lattice/target scene.

Sequential dependency: A is the canonical mask transfer; the intermediate is the
cyan target-coordinate mask; B finds zero regions that are enclosed in that
intermediate and fills them. `skip_transfer.rkt` runs B on a blank intermediate
and therefore removes the input-dependent topology B needs.
Re-run the bounded authoring audit with:

```sh
python3 generators/c286f4a2923f/workspace/parametric/audit.py
```

It checks matched/prefix-stable episodes, sequential public-view privacy, the
30×30 stress case, and six named shortcuts. It does not replace protected
qualification or owner acceptance.
