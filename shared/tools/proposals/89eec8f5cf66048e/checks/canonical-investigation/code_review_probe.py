#!/usr/bin/env python3
"""Independent finite-domain arithmetic checks of the selected bounded repair."""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import traceback

from reviewer_support import load_selected_generator
from mutation_probe import scan, dump, ROOT, OUT, TASK


def main():
    gen, source, digest = load_selected_generator(TASK, root=ROOT)
    census=json.loads((OUT / "structural-patch-census.json").read_text())
    expected={(row["profile_index"],row["transform"]):row["minimal_patch"] for row in census["templates"] if row["minimal_patch"]}
    checked_edits=[]
    for ident, edits in gen._STRUCTURAL_EDITS.items():
        required=tuple((r,c,after) for r,c,before,after in expected[ident]["changes"])
        assert edits == required, (ident,edits,required)
        template=gen._TEMPLATES[ident]
        assert all((r,c) in template["protected"] and (r,c) not in template["bit_positions"] and template["grid"][r][c] != 2 and value != 2 for r,c,value in edits)
        checked_edits.append(list(ident))
    assert len(checked_edits)==21

    contexts={}
    context_counts=Counter()
    budget_min,slack_min=1000,1000
    for code in range(gen.SCENE_COUNT):
        template=gen._template_for_code(code)
        ident=(template["profile_index"],template["transform_index"])
        altered=code % 5 in (1,3)
        context=(*ident,altered)
        contexts.setdefault(context,code)
        context_counts[context]+=1
        if code in gen._ANCHOR_PROFILE_BY_CODE:
            continue
        gray=sum(template["grid"][r][c]==5 for r,c in template["protected"])
        if altered:
            gray+=sum((value==5)-(template["grid"][r][c]==5) for r,c,value in gen._STRUCTURAL_EDITS[ident])
        needed=gen._target_gray_count(code)-gray-code.bit_count()
        available=len(template["safe"])-gen.CODE_BITS
        assert 0<=needed<=available,(code,needed,available)
        budget_min=min(budget_min,needed)
        slack_min=min(slack_min,available-needed)
    assert len(contexts)==53

    representatives=[]
    center_masks=defaultdict(set)
    for context,code in contexts.items():
        grid=gen.generate(-1,2**65+17,difficulty="hard",scene_code=code)
        assert gen.self_check(grid)==[],(code,gen.self_check(grid))
        assert gen.observe_overrides(grid)=={"scene_code":code}
        independent=scan(grid)[2]
        assert gen.rule_mirror(grid)==independent
        disagrees=gen.red_layout_lookup(grid)!=independent
        assert disagrees==context[2],(context,code)
        centers=tuple((r,c) for r in range(19) for c in range(19) if independent[r][c]==4)
        center_masks[gen._red_key(grid)].add(centers)
        representatives.append({"context":list(context),"scene_code":code,"legacy_lookup_refuted":disagrees})
    assert len(center_masks)==32
    assert sum(len(x)==2 for x in center_masks.values())==21
    assert sum(len(x)==1 for x in center_masks.values())==11

    seeds=(-2**96-17,-1,0,17,2**32,169446987945668,2**96+17)
    indexes=(0,1,6551,6552,6553,32763,32764,32765,2**70+19)
    bands=(None,"easy","medium","hard")
    periodicity_checks=0
    holdout_checks=0
    natural_generation_checks=0
    for seed in seeds:
        for band in bands:
            for index in indexes:
                first=gen._natural_scene_code(seed,index,band)
                repeated=gen._natural_scene_code(seed,index+gen.SCENE_COUNT,band)
                assert first==repeated
                periodicity_checks+=1
                lanes=[gen._natural_scene_code(seed,index+j,band)%5 for j in range(6)]
                assert sum(lane in (1,3) for lane in lanes[:5])==2
                for held_out in range(6):
                    assert sum(lane in (1,3) for j,lane in enumerate(lanes) if j!=held_out)>=1
                    holdout_checks+=1
            for index in (0,6552,32764,2**70+19):
                grid=gen.generate(seed,index,difficulty=band)
                code=gen._natural_scene_code(seed,index,band)
                assert gen.observe_overrides(grid)=={"scene_code":code}
                assert gen.strict_canonical_like(grid)==[]
                natural_generation_checks+=1
    for kwargs in ({"seed":True,"sample_index":0},{"seed":0,"sample_index":True},{"seed":0,"sample_index":-1}):
        try:
            gen.generate(**kwargs)
        except (TypeError,ValueError):
            pass
        else:
            raise AssertionError(("invalid scalar accepted",kwargs))
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    result={
        "schema":"fc814cec3976-independent-code-domain-check-v1",
        "generator_sha256":digest,"version":gen.VERSION,
        "source_unchanged_during_probe":hashlib.sha256(source.read_bytes()).hexdigest()==digest,
        "verified_structural_edit_count":len(checked_edits),
        "all_scene_gray_budgets_checked":gen.SCENE_COUNT,
        "minimum_gray_additions":budget_min,"minimum_unused_safe_cells":slack_min,
        "red_layout_count":len(center_masks),"context_count":len(contexts),
        "layouts_with_two_center_masks":sum(len(x)==2 for x in center_masks.values()),
        "layouts_with_one_center_mask":sum(len(x)==1 for x in center_masks.values()),
        "representatives":representatives,
        "natural_generation_checks":natural_generation_checks,
        "large_negative_seed_and_wrap_periodicity_checks":periodicity_checks,
        "query_holdout_lane_checks":holdout_checks,
        "fixed_seed_period":math.lcm(gen.VARIANT_COUNT,5),
        "variant_step_coprime_to_variant_count":math.gcd(89,gen.VARIANT_COUNT)==1,
        "schedule_proof":"For any integer seed, nonnegative integer index and supported band, lane=(seed+index+band_index)%5. Every5consecutive lanes contain1and3; every6 contain at least2altered scenes, so any single held-out role leaves at least1altered demonstration. This does not depend on the variant quotient or modulo6553 wrap.",
        "racket_scope":"No new Racket labels in this review probe. All21hardcoded structural edits were checked byte-for-byte against the prior48-input canonical Racket diagnostic; the current Python mirror is unchanged in implementation and agreed with an independent scanner on53representative generated contexts.",
    }
    dump("code-domain-review.json",result)
    print(json.dumps({k:result[k] for k in ("generator_sha256","source_unchanged_during_probe","all_scene_gray_budgets_checked","context_count","layouts_with_two_center_masks","natural_generation_checks","large_negative_seed_and_wrap_periodicity_checks","query_holdout_lane_checks")}),flush=True)


if __name__=="__main__":
    command={"argv":sys.argv,"python":sys.executable,"cwd":str(ROOT),"started_utc":datetime.now(timezone.utc).isoformat()}
    try:
        main()
    except BaseException as exc:
        command.update(exit_code=1,error=str(exc),traceback=traceback.format_exc())
        dump("code-domain-command.json",command)
        raise
    else:
        command.update(exit_code=0,finished_utc=datetime.now(timezone.utc).isoformat())
        dump("code-domain-command.json",command)
