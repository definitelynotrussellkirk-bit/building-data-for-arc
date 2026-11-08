#!/usr/bin/env python3
"""Report recorded battery statuses without executing gates (standard library)."""
import argparse
import json
import sys
from pathlib import Path

STATUSES = ("green", "advisory", "failed", "interrupted", "pending", "running")


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def nonfinite(value):
    raise ValueError("nonfinite JSON constant: " + value)


def summarize(document):
    """Accept generator_battery_summary/1 or an embedded public check result."""
    public = document.get("schema") == "arcpuzzles-check-v1"
    battery = document.get("battery_summary") if public else document
    if not isinstance(battery, dict) or battery.get("schema") != "generator_battery_summary/1":
        raise ValueError("expected generator_battery_summary/1 or public result with embedded summary")
    stages = battery.get("stages")
    if not isinstance(stages, dict) or not stages:
        raise ValueError("stages must be a nonempty object")
    by_status = {status: [] for status in STATUSES}
    for name, entry in stages.items():
        if not isinstance(entry, dict) or entry.get("status") not in by_status:
            raise ValueError("unknown or missing status for stage %s" % name)
        by_status[entry["status"]].append(name)
    counts = {status: len(names) for status, names in by_status.items()}
    counts["total"] = len(stages)
    recorded_counts = battery.get("counts")
    if (not isinstance(recorded_counts, dict)
            or any(type(value) is not int or value < 0 for value in recorded_counts.values())
            or recorded_counts != counts):
        raise ValueError("recorded counts disagree with stage statuses")
    unfinished = sum(counts[key] for key in ("interrupted", "pending", "running"))
    complete = unfinished == 0
    nonblocking = complete and counts["failed"] == 0
    all_green = nonblocking and counts["advisory"] == 0
    verdict = ("FAIL" if counts["failed"] else "INCOMPLETE" if unfinished else
               "ADVISORY" if counts["advisory"] else "PASS")
    expected = {"FAIL": "failed", "INCOMPLETE": "incomplete",
                "ADVISORY": "passed_with_advisories", "PASS": "all_green"}[verdict]
    recorded_verdict = battery.get("verdict")
    # A live owner can report running ahead of unfinished-stage precedence.
    if (recorded_verdict is not None and recorded_verdict != expected
            and not (recorded_verdict == "running" and unfinished)):
        raise ValueError("recorded verdict contradicts stage statuses")
    result = {
        "task": battery.get("task"), "phase": battery.get("phase"),
        "verdict": verdict, "recorded_verdict": battery.get("verdict"),
        "counts": {"PASS": counts["green"], "ADVISORY": counts["advisory"],
                   "FAIL": counts["failed"], "UNFINISHED": unfinished, "TOTAL": counts["total"]},
        "complete": complete, "completed_nonblocking": nonblocking,
        "every_stage_green": all_green, "advisory_stages": by_status["advisory"],
        "failed_stages": by_status["failed"],
        "unfinished_stages": {key: by_status[key] for key in ("interrupted", "pending", "running")},
    }
    if public:
        if (type(document.get("exit_code")) is not int
                or type(document.get("timed_out", False)) is not bool):
            raise ValueError("public exit_code and timed_out need integer and Boolean types")
        result["public_exit_code"] = document.get("exit_code")
        result["public_status"] = document.get("status")
        result["completed_nonblocking_exit0"] = (
            nonblocking and document.get("exit_code") == 0
            and document.get("status") == "completed" and not document.get("timed_out", False))
    else:
        result["completed_nonblocking_exit0"] = None  # No invocation exit code in raw summary.
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="battery summary JSON or public result.json")
    parser.add_argument("--json", action="store_true", help="emit compact structured report")
    args = parser.parse_args(argv)
    try:
        result = summarize(json.loads(args.input.read_text(), object_pairs_hook=unique_pairs,
                                      parse_constant=nonfinite))
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print("ERROR: %s" % error, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("%s: %s (%s)" % (result["verdict"], result["task"], result["phase"]))
        print(" / ".join("%s=%s" % (key, value) for key, value in result["counts"].items()))
        print("Completed nonblocking: %s; every stage green: %s" %
              (result["completed_nonblocking"], result["every_stage_green"]))
        print("Completed nonblocking exit 0: %s" % result["completed_nonblocking_exit0"])
        if result["advisory_stages"]:
            print("Advisory stages: " + ", ".join(result["advisory_stages"]))
    return 1 if result["verdict"] in ("FAIL", "INCOMPLETE") else 0


if __name__ == "__main__":
    raise SystemExit(main())
