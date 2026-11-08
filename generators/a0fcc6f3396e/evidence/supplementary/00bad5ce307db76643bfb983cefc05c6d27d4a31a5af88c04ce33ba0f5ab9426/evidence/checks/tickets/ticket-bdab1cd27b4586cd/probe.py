from __future__ import annotations

import hashlib
import json
from pathlib import Path

TICKET_ID = "ticket-bdab1cd27b4586cd"
PROBE_SEED = "623c9a707f0f7fe6aa3b3436638fd0201798f505bce1558033917d6a09667d05"
EXPECTED_GENERATOR_SHA256 = "20ca95cb86ac5682dec158411ede8f77347e6105922a731d612ea2f66cfe39fd"
EXPECTED_MANIFEST_SHA256 = "1ab66f44f6c1a70122df4a4263be4c1de3a39812b5191944c0635e21d99a107c"
GENERATOR = Path("generators/a0fcc6f3396e/generator.py")
BASE = Path("generators/a0fcc6f3396e/workspace/parametric/evidence")
MANIFEST = BASE / "manifest.json"
FINAL = BASE / "final-run"
OUT = Path("../checks/tickets") / TICKET_ID / "result.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    generator_sha = sha256(GENERATOR)
    manifest_sha = sha256(MANIFEST)
    if generator_sha != EXPECTED_GENERATOR_SHA256:
        raise SystemExit(f"generator hash mismatch: {generator_sha}")
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise SystemExit(f"manifest hash mismatch: {manifest_sha}")

    final = json.loads((FINAL / "result.json").read_text())
    checks: list[dict] = []
    settings = []
    for episode in final["episodes"]:
        public_path = FINAL / episode["public_path"]
        private_path = FINAL / episode["private_path"]
        public = json.loads(public_path.read_text())
        private = json.loads(private_path.read_text())
        setting = private["parameters"]["output_color"]
        settings.append(setting)

        public_shape_ok = (
            set(public) == {"train", "test"}
            and len(public["train"]) == 3
            and len(public["test"]) == 1
            and all(set(pair) == {"input", "output"} for pair in public["train"])
            and all(set(pair) == {"input"} for pair in public["test"])
        )
        private_boundary_ok = (
            set(private["parameters"]) == {"output_color"}
            and isinstance(private.get("program"), str)
            and len(private.get("test_outputs", [])) == 1
            and "output" not in public["test"][0]
            and "parameters" not in public
            and "program" not in public
            and "test_outputs" not in public
        )
        hashes_ok = (
            sha256(public_path) == episode["public_sha256"]
            and sha256(private_path) == episode["private_sha256"]
            and private["public_sha256"] == episode["public_sha256"]
        )
        rival_identifies_setting = (
            private["rivals"][str(setting)]["status"] == "survived_all"
            and all(
                row["status"] == "refuted_by_demonstrations"
                for key, row in private["rivals"].items()
                if int(key) != setting
            )
        )
        checks.append({
            "seed": episode["seed"],
            "output_color": setting,
            "public_three_demos_one_query": public_shape_ok,
            "private_setting_program_and_query_answer_only": private_boundary_ok,
            "recorded_hashes_match": hashes_ok,
            "demonstrations_identify_setting": rival_identifies_setting,
        })

    supported = (
        final.get("status") == "prototype_passed"
        and set(settings) == {3, 8}
        and set(final.get("settings_covered", [])) == {3, 8}
        and not final.get("missing_episode_settings")
        and all(all(value for key, value in row.items() if key not in {"seed", "output_color"}) for row in checks)
    )
    result = {
        "ticket_id": TICKET_ID,
        "task_id": final["task_id"],
        "probe_seed": PROBE_SEED,
        "generator_sha256": generator_sha,
        "evidence_manifest_sha256": manifest_sha,
        "status": "completed" if supported else "finding",
        "checks": checks,
        "settings_covered": sorted(settings),
        "query_count": len(checks),
        "support_conclusion": (
            "The retained prototype supports both declared settings with three visible demonstrations and one hidden-answer query per setting; setting, program text, and query answers remain private."
            if supported
            else "The retained prototype failed at least one setting/count/privacy boundary check."
        ),
        "approval_boundary": "This is source-bound prototype support only; it does not approve the color-3 variant or modify the production generator.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "settings": result["settings_covered"],
        "episodes": len(checks),
        "output": str(OUT),
    }, sort_keys=True))
    if not supported:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
