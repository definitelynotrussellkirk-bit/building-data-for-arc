"""One source-bound valid/invalid scene_profile boundary; no safety approval."""
import hashlib
import json
from pathlib import Path
import time
from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
TASK = "809c8b84e40a"
TICKET = "ticket-13805edc3673fd08"
SEED_HEX = "60461ca7ddfe863b9d3f11014c4be24fb653c0704be825fbb40e39e42ad48c5f"
EXPECTED = "bc11ff668c51dc1f673f920fdf01559dc45cdc39a717e3508306208714c211dd"
start = time.monotonic()
module, source, digest = load_selected_generator(TASK, root=ROOT)
assert digest == EXPECTED, "Pinned source changed"
seed = int(SEED_HEX[:16], 16)
choices = module.AXES["scene_profile"]["valid"]
profile = choices[seed % len(choices)]
valid = module.generate(seed, 0, scene_profile=profile)
observed = module.observe_overrides(valid)
errors = module.self_check(valid)
assert observed["scene_profile"] == profile and not errors
invalid = "__not_an_advertised_profile__"
try:
    module.generate(seed, 0, scene_profile=invalid)
except ValueError as error:
    rejection = {"type": type(error).__name__, "message": str(error)}
else:
    raise AssertionError("Invalid scene_profile was silently accepted")
row = {
    "ticket_id": TICKET, "type": "api_boundary", "status": "completed",
    "summary": "Advertised scene_profile " + profile + " was honored exactly and passed its structural self_check; an unknown profile was rejected with ValueError. No issue found in this single boundary comparison.",
    "evidence_paths": ["checks/tickets/" + TICKET + "/probe.py", "checks/tickets/" + TICKET + "/result.json"],
    "elapsed_minutes": None,
    "task_id": TASK, "probe_seed": SEED_HEX, "generator_seed": seed,
    "source": {"path": str(source.relative_to(ROOT)), "sha256": digest},
    "rule_hash": "a9ac01cfb199",
    "valid": {"requested_scene_profile": profile, "observed": observed,
              "shape": [len(valid), len(valid[0])], "self_check": errors,
              "input_sha256": hashlib.sha256(json.dumps(valid, sort_keys=True, separators=(",", ":")).encode()).hexdigest()},
    "invalid": {"scene_profile": invalid, "rejection": rejection},
    "probe_seconds": time.monotonic() - start,
    "limits": "One advertised override boundary only; no Racket label check, peer battery, audit resolution or safety claim.",
}
Path(__file__).with_name("result.json").write_text(json.dumps(row, indent=2, sort_keys=True)+"\n")
print(json.dumps(row, indent=2, sort_keys=True))
