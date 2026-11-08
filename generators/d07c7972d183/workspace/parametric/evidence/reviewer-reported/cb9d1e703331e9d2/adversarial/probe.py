"""Bounded independent demo-certificate and export/type adversarial probe."""
import copy, hashlib, importlib.util, json, sys, tempfile, time
from pathlib import Path
from unittest.mock import patch
import numpy as np

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent.parent / "repo"
SOURCE = ROOT / "generators/d07c7972d183/workspace/parametric/prototype.py"
spec = importlib.util.spec_from_file_location("adversarial_subject", SOURCE)
p = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = p
spec.loader.exec_module(p)
started = time.monotonic()
checks = []
def record(name, passed, detail=None):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})
def reject(name, fn, expected=(ValueError,)):
    try:
        fn()
    except expected as error:
        record(name, True, type(error).__name__ + ": " + str(error))
        return
    except Exception as error:
        record(name, False, "unexpected " + type(error).__name__ + ": " + str(error))
        return
    record(name, False, "accepted invalid value")
class Spy:
    def __init__(self, live):
        self.live, self.calls = live, []
    def apply(self, source, grid):
        self.calls.append(copy.deepcopy(grid))
        return self.live.apply(source, grid)

with p.RacketRunner() as runner:
    episodes = [p.generate_episode(17, settings=s, demos=2, queries=1, runner=runner)
                for s in p.SETTINGS]
    record("four_settings_two_demos_refute_all_seven", all(
        ep["certificate"]["surviving_settings"] == [ep["settings"]]
        and not ep["certificate"]["surviving_shortcuts"]
        and all(ep["certificate"]["shortcut_rejections"].values()) for ep in episodes))
    base = episodes[0]
    for field in p.DEFAULT:
        for value in (True, False, np.int64(2), np.int32(3), np.float64(2), 2.0, "2"):
            reject("setting_%s_rejects_%s_%s" % (field, type(value).__name__, str(value)),
                   lambda field=field, value=value: p.program(dict(p.DEFAULT, **{field: value})))
    for field in ("seed", "input_seed", "demos", "queries"):
        for value in (True, np.int64(2), 2.0, "2"):
            args = dict(seed=1, demos=2, queries=1, runner=runner)
            args[field] = value
            reject("control_%s_rejects_%s_%s" % (field, type(value).__name__, str(value)),
                   lambda args=args: p.generate_episode(**args))
    for value in (True, np.int64(1), 1.0):
        changed = copy.deepcopy(base)
        changed["test"][0]["input"][0][0] = value
        reject("public_cell_rejects_" + type(value).__name__,
               lambda changed=changed: p.public_challenge_bytes(changed))

    # A query that exposes aliases cannot rescue ambiguous demonstrations.
    ambiguous = copy.deepcopy(p.canonical_record()["train"][:2])
    query = copy.deepcopy(base["train"][0]["input"])
    spy = Spy(runner)
    reject("ambiguous_demos_rejected", lambda: p.lesson_certificate(
        ambiguous, [query], p.DEFAULT, spy))
    record("ambiguous_demos_do_not_execute_query", all(g != query for g in spy.calls),
           {"executions": len(spy.calls)})

    # An alternative runtime failure must propagate, never refute that rival.
    rivals = p.rival_programs(p.DEFAULT)
    rivals["repeat_input"] = "(rule! (lambda (g) (/ 1 0)))"
    with patch.object(p, "rival_programs", return_value=rivals):
        try:
            p.lesson_certificate(base["train"], [base["test"][0]["input"]], p.DEFAULT, runner)
        except Exception as error:
            record("rival_runtime_failure_rejected", True, type(error).__name__ + ": " + str(error))
        else:
            record("rival_runtime_failure_rejected", False, "runtime error accepted as refutation")

    hidden = copy.deepcopy(base)
    hidden.update(seed=992, input_seed=37, settings={"hidden": "canary"},
                  program_solution="PRIVATE_CANARY", arbitrary_private="PRIVATE_CANARY")
    hidden["test"][0]["output"] = [[9]]
    hidden["train"][0]["private_note"] = "PRIVATE_CANARY"
    visible = p.public_challenge_bytes(hidden)
    record("private_metadata_and_query_labels_do_not_change_public", visible == p.public_challenge_bytes(base))
    record("public_id_is_exact_written_bytes_sha256",
           p.public_challenge_id(hidden) == hashlib.sha256(visible).hexdigest())
    record("no_private_canary_in_projection", b"PRIVATE_CANARY" not in visible)

    with tempfile.TemporaryDirectory(prefix="attack-", dir=BASE) as tmp:
        parent = Path(tmp)
        changes = {
            "program_text": lambda ep: ep.update(program_solution=ep["program_solution"] + "\n"),
            "program_hash_path": lambda ep: ep.update(program_sha256="../escape"),
            "source_hashes": lambda ep: ep["source_hashes"].update(forged="0" * 64),
            "runtime": lambda ep: ep["racket_runtime"].update(protected=False),
            "certificate": lambda ep: ep["certificate"].update(queries=[]),
        }
        for key, alter in changes.items():
            changed = copy.deepcopy(base)
            alter(changed)
            destination = parent / key
            reject("reject_forged_" + key,
                   lambda changed=changed, destination=destination: p.write_export([changed], destination, runner=runner))
            record("forged_" + key + "_leaves_no_destination", not destination.exists())
        destination = parent / "valid"
        manifest = p.write_export(episodes, destination, runner=runner)
        actual = (destination / "public.jsonl").read_bytes()
        expected = b"".join(p.public_challenge_bytes(ep) for ep in sorted(episodes, key=p.public_challenge_id))
        record("valid_export_sorted_exact_public_bytes", actual == expected)
        record("valid_export_manifest_hashes", all(
            hashlib.sha256((destination / name).read_bytes()).hexdigest() == value
            for name, value in manifest["files"].items()))
        record("valid_export_public_names_bind_bytes", all(
            path.stem == hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (destination / "public").iterdir()))
        # All Python-private data travels through serialization before committing output.
        changed = copy.deepcopy(base)
        changed["arbitrary_private"] = {"not_json"}
        destination = parent / "non_json_private"
        try:
            p.write_export([changed], destination, runner=runner)
        except Exception as error:
            left = sorted(str(x.relative_to(destination)) for x in destination.rglob("*")) if destination.exists() else []
            record("invalid_private_metadata_rejected_before_destination", not destination.exists(),
                   {"error": type(error).__name__ + ": " + str(error), "partial_paths": left})
        else:
            record("invalid_private_metadata_rejected_before_destination", False, "unexpected success")
    runtime = runner.identity
    evaluations = runner.evaluations
result = {"scope": "bounded independent two-surface adversarial probe; no full battery",
          "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "elapsed_seconds": round(time.monotonic() - started, 3),
          "racket_runtime": runtime, "racket_evaluations": evaluations,
          "passed": sum(c["passed"] for c in checks), "checks": len(checks),
          "findings": [c for c in checks if not c["passed"]], "details": checks}
(BASE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: result[k] for k in ("source_sha256", "elapsed_seconds", "checks", "passed", "findings")}, indent=2))
