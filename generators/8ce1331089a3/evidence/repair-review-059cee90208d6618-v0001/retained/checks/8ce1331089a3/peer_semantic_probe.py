"""Bounded optional peer audit: two native-labeled three-demo/four-query lessons."""
from collections import Counter
from pathlib import Path
import hashlib
import json

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import load_selected_generator

ROOT = Path(__file__).resolve().parents[2] / "repo"
TASK = "8ce1331089a3"
OUT = Path(__file__).with_name("peer_semantic_audit.json")
if OUT.exists():
    raise FileExistsError(OUT)

def alternative(g, kind):
    h, w = len(g), len(g[0])
    colors = [g[0][1], g[h-1][1], g[1][0], g[1][w-1]]
    counts = Counter(g[r][c] for r in range(1, h-1) for c in range(1, w-1))
    out = [[g[r][c] if r in (0, h-1) or c in (0, w-1) else 0
            for c in range(w)] for r in range(h)]
    for r in range(1, h-1):
        for c in range(1, w-1):
            v = g[r][c]
            if v not in colors or (kind == "drop_interior_singletons" and counts[v] == 1):
                continue
            options = [(1,c), (h-2,c), (r,1), (r,w-2)]
            if kind in ("nearest_edge", "farthest_edge"):
                choose = min if kind == "nearest_edge" else max
                dst = choose(options, key=lambda x: abs(r-x[0]) + abs(c-x[1]))
            else:
                side = colors.index(v)
                if kind == "reflect_perpendicular":
                    options = [(1,w-1-c), (h-2,w-1-c), (h-1-r,1), (h-1-r,w-2)]
                dst = options[side]
            out[dst[0]][dst[1]] = v
    return out

def alternative_program(kind):
    normal = "(cond ((= v (nth colors 0)) (list 1 c)) ((= v (nth colors 1)) (list (- h 2) c)) ((= v (nth colors 2)) (list r 1)) (else (list r (- w 2))))"
    reflected = "(cond ((= v (nth colors 0)) (list 1 (- w 1 c))) ((= v (nth colors 1)) (list (- h 2) (- w 1 c))) ((= v (nth colors 2)) (list (- h 1 r) 1)) (else (list (- h 1 r) (- w 2))))"
    if kind in ("nearest_edge", "farthest_edge"):
        pick = "pick-min" if kind == "nearest_edge" else "pick-max"
        destination = f"({pick} (list (list 1 c) (list (- h 2) c) (list r 1) (list r (- w 2))) (lambda (p) (+ (abs (- r (nth p 0))) (abs (- c (nth p 1))))))"
    else:
        destination = reflected if kind == "reflect_perpendicular" else normal
    condition = "(member v colors)"
    if kind == "drop_interior_singletons":
        condition = "(and (member v colors) (> (length (filter (lambda (rc) (= (at g (nth rc 0) (nth rc 1)) v)) coords)) 1))"
    return f"""(rule! (lambda (g)
      (let* ((h (rows g)) (w (cols g))
             (colors (list (at g 0 1) (at g (- h 1) 1) (at g 1 0) (at g 1 (- w 1))))
             (result (make-hash))
             (coords (apply append (map (lambda (r) (map (lambda (c) (list r c)) (range 1 (- w 1)))) (range 1 (- h 1))))))
        (for* ((r (range 0 h)) (c (range 0 w)))
          (hash-set! result (list r c) (if (or (= r 0) (= r (- h 1)) (= c 0) (= c (- w 1))) (at g r c) 0)))
        (for* ((r (range 1 (- h 1))) (c (range 1 (- w 1))))
          (let ((v (at g r c))) (when {condition}
            (hash-set! result {destination} v))))
        (cellmap g (r c v) (hash-ref result (list r c) 0))))))"""

report = {"schema": "arcpuzzles-bounded-peer-semantic-review-v1", "task_id": TASK,
          "scope": {"seeds": [0,17], "sample_indices": list(range(7)),
                    "difficulty": None, "demos": 3, "queries": 4,
                    "additional_checks": "sliding three-demo/one-query windows in each seven-pair sequence"},
          "findings": [], "errors": [], "lessons": [], "pairs": [], "racket": None,
          "remaining_limits": ["Finite rivals and two default lessons only; no universal identifiability claim.",
                               "No override sweep, difficulty sweep, full battery, parametric work, or approval change.",
                               "The five retained rival functions are checked in Python against executed canonical labels."]}
native_names = ["nearest_edge", "farthest_edge", "reflect_perpendicular", "drop_interior_singletons"]
runtime = ROOT / "shared/runtime"
with _local_imports(runtime, runtime):
    module, source, digest = load_selected_generator(TASK, root=ROOT)
    canonical = Catalog(ROOT).get(TASK)["variants"][0]["program_solution"]
    programs = {"canonical": canonical, **{name: alternative_program(name) for name in native_names}}
    report["source_binding"] = {"generator_path": str(source.relative_to(ROOT)), "generator_sha256": digest,
                                "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    report["programs"] = {name: {"text": p, "sha256": hashlib.sha256(p.encode()).hexdigest()} for name,p in programs.items()}
    apply, identity, bridge = _real_evaluator(runtime)
    report["racket"] = identity
    report["rivals"] = list(module.SEMANTIC_RIVALS) + native_names
    calls = 0
    try:
        for seed in (0,17):
            pairs, outputs = [], []
            for index in range(7):
                g = module.generate(seed,index)
                assert not module.self_check(g)
                answer = _grid(apply(canonical,g)); calls += 1
                assert answer == module.rule_mirror(g), "canonical mirror mismatch"
                rival_values = {name: fn(g) for name,fn in module.SEMANTIC_RIVALS.items()}
                for name in native_names:
                    value = _grid(apply(programs[name],g)); calls += 1
                    assert value == alternative(g,name), "Racket/Python rival mismatch: " + name
                    rival_values[name] = value
                pair = {"seed":seed,"sample_index":index,"input":g,"output":answer,
                        "rival_disagreements":{name:value != answer for name,value in rival_values.items()}}
                pairs.append(pair); outputs.append(rival_values); report["pairs"].append(pair)
            windows = [(0,[3,4,5,6])] + [(start,[start+3]) for start in range(1,4)]
            for start,queries in windows:
                survivors = [name for name in report["rivals"] if all(outputs[i][name] == pairs[i]["output"] for i in range(start,start+3))]
                finding_names = [name for name in survivors if any(outputs[i][name] != pairs[i]["output"] for i in queries)]
                lesson = {"seed":seed,"demonstration_indices":list(range(start,start+3)),
                          "query_indices":queries,"surviving_rivals":survivors,"actionable_rivals":finding_names}
                report["lessons"].append(lesson)
                if finding_names:
                    report["findings"].append(lesson)
                print(json.dumps(lesson),flush=True)
    except Exception as error:
        report["errors"].append(repr(error))
        print(json.dumps({"error":repr(error)}),flush=True)
    finally:
        bridge.close()
    report["source_stable"] = hashlib.sha256(source.read_bytes()).hexdigest() == digest
    report["protected_racket_evaluations"] = calls
report["outcome"] = "unchanged" if not report["errors"] else "blocked"
report["finite_no_issue"] = not report["errors"] and not report["findings"]
OUT.write_text(json.dumps(report, separators=(",",":")) + "\n")
print(json.dumps({"report":str(OUT),"outcome":report["outcome"],"pairs":len(report["pairs"]),
                  "lessons":len(report["lessons"]),"racket_evaluations":report["protected_racket_evaluations"],
                  "findings":len(report["findings"]),"errors":report["errors"]}),flush=True)
