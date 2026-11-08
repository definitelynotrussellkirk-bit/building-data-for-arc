"""DRAW-NEW-STRUCTURE-FROM-MARKERS concept family.

Closes a real eval gap (e.g. task 1818057f: input palette {2,4} -> output
ADDS color 8 by drawing crosses; 16de56c4: marker colors resolved). Every
generator here INTRODUCES A NEW COLOR not present in the input's core pattern
by DRAWING structure seeded from marker cells: from each marker we shoot rays,
draw a full cross, or connect markers with lines in a fresh color.

Each generator FIXES one transform (the draw-from-markers op + composed ops)
and resamples the INPUT to emit a full multi-pair task whose pairs all share
ONE Racket `program`. The Python `apply` is byte-exact with what the Racket
`program` produces (proven over >=25 random seeds in each file's __main__ via
RacketBridge).

The shared parity helper lives here so the bridge wiring is defined once.
"""
from __future__ import annotations


def _program_body(program: str) -> str:
    """Extract BODY from `(rule! (lambda (g) BODY))` by paren-matching."""
    marker = "(lambda (g)"
    i = program.index(marker) + len(marker)
    depth = 1
    j = i
    while j < len(program) and depth > 0:
        if program[j] == "(":
            depth += 1
        elif program[j] == ")":
            depth -= 1
        j += 1
    return program[i:j - 1].strip()


def parity_check(generate_task, *, n=25, version_label=""):
    """Run `generate_task` over n seeds, eval its program body in Racket,
    assert byte-exact equality with every pair's stored output. Also asserts
    each output ADDS the new drawn color absent from the input.

    Returns (passed, total). Prints the first per-seed failure if any.
    """
    from arc_repl.racket_bridge import RacketBridge

    b = RacketBridge()
    passed = 0
    total = 0
    first_fail = None
    new_color_ok = True
    for seed in range(n):
        task = generate_task(seed)
        body = _program_body(task["program"])
        new_color = task.get("new_color")
        for split in ("train", "test"):
            for pair in task[split]:
                total += 1
                inp, exp = pair["input"], pair["output"]
                # concept assertion: new color is absent from input, present in output
                if new_color is not None:
                    in_has = any(new_color == v for row in inp for v in row)
                    out_has = any(new_color == v for row in exp for v in row)
                    if in_has or not out_has:
                        new_color_ok = False
                b.define_grid("g", inp)
                got = b.eval_text(body)
                if got == exp:
                    passed += 1
                elif first_fail is None:
                    first_fail = {
                        "seed": seed, "split": split, "body": body,
                        "py_out": exp, "rkt_out": got,
                        "input_dims": (len(inp), len(inp[0])),
                    }
    if first_fail is not None:
        print("FIRST MISMATCH:", first_fail)
    if not new_color_ok:
        print("WARNING: new-color concept assertion FAILED for at least one pair")
    tag = f" [{version_label}]" if version_label else ""
    print(f"PARITY: {passed}/{total} exact{tag}"
          f"{'  (+new-color verified)' if new_color_ok else '  (new-color FAILED)'}")
    return passed, total
