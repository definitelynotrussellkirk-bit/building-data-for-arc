"""EXTRACTION concept family: large grid -> much smaller output.

Closes the eval gap on tasks like 0934a4d8 (30x30 -> 9x4) and
20a9e565 (30x30 -> 3x6): the output is a small region/object pulled
out of a big, distractor-laden input.

Each generator FIXES one transform (extraction + composed ops) and
resamples the INPUT to emit a full multi-pair task whose pairs all
share ONE Racket `program`. The Python `apply` is byte-exact with what
the Racket `program` produces (proven over >=25 random seeds in each
file's __main__ via RacketBridge).

Shared parity helper lives here so the bridge wiring is defined once.
"""
from __future__ import annotations


def parity_check(generate_task, *, n=25, version_label=""):
    """Run `generate_task` over n seeds, eval its program body in Racket,
    assert byte-exact equality with every pair's stored output.

    Returns (passed, total). Prints the per-seed first failure if any.
    The program is `(rule! (lambda (g) BODY))`; we eval BODY directly
    against a freshly-defined `g` in the bridge.
    """
    from arc_repl.racket_bridge import RacketBridge

    b = RacketBridge()
    passed = 0
    total = 0
    first_fail = None
    for seed in range(n):
        task = generate_task(seed)
        body = _program_body(task["program"])
        for split in ("train", "test"):
            for pair in task[split]:
                total += 1
                b.define_grid("g", pair["input"])
                got = b.eval_text(body)
                if got == pair["output"]:
                    passed += 1
                elif first_fail is None:
                    first_fail = {
                        "seed": seed, "split": split, "body": body,
                        "py_out": pair["output"], "rkt_out": got,
                        "input_dims": (len(pair["input"]), len(pair["input"][0])),
                    }
    if first_fail is not None:
        print("FIRST MISMATCH:", first_fail)
    tag = f" [{version_label}]" if version_label else ""
    print(f"PARITY: {passed}/{total} exact{tag}")
    return passed, total


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
