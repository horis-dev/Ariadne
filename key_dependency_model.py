import math
import random
import msgspec
from typing import List, Dict, Any
from word_lib import WordLib, WordPosition, LocalWordlib
from basic.position import ApiPosition
from api.api_node import ApiNode
from loguru import logger

from basic.fuzzword import FuzzWord, MutateValue
from basic.seed import SeedInput


class KeyDependencyModelData(msgspec.Struct, tag="KeyDependencyModelData"):
    init_word_lib: WordLib = None
    target_word_lib: WordLib = None
    all_api_positions: List[ApiPosition] = []
    optional_api_mutation_probability: float = 0.5
    init_wordlib_mutation_probability: float = 0.5
    p_use_dependency: float = 0.9
    p_local_wordlib: float = 0.9
    p_target_wordlib: float = 0.8
    p_optional_pos: float = 0.5


class KeyDependencyModel:
    DEFAULTS = {
        'optional_api_mutation_probability': 0.5,
        'init_wordlib_mutation_probability': 0.5,
        'p_optional_pos': 0.5,  # Probability of mutating optional fields
        'p_use_dependency': 0.8,
        # Probability of selecting a Position from the dependency graph (otherwise select itself)
        'p_local_wordlib': 1.0,
        # Priority coefficient for choosing values from local word library during mutation (max 1)
        'p_target_wordlib': 1.0,  # Priority coefficient for choosing values from the target word library (max 1)
    }

    def __init__(self, data: KeyDependencyModelData):
        """ Model based on normal-traffic corpora to generate a dependency graph. """
        self.init_word_lib = data.init_word_lib
        self.target_word_lib = data.target_word_lib
        self.all_api_positions = data.all_api_positions
        self.dependency_graph = self.gen_dependency_graph(self.all_api_positions)
        self.output_dependency_html()  # print dependency graph
        for key, default in self.DEFAULTS.items():
            setattr(self, key, self._validate_probability(getattr(data, key), default))

    def _validate_probability(self, value: float, default: float):
        """ Validate that the input probability is between 0 and 1; otherwise return the default. """
        return value if 0 <= value <= 1 else default

    def gen_dependency_graph(
            self,
            key_positions: List[ApiPosition],
    ) -> Dict[ApiPosition, Dict[WordPosition, dict]]:
        dependency_graph = {}
        for wp in key_positions:
            # Get all similarities with the current WordPosition
            similarities = self.init_word_lib.get_all_similarities(wp)
            if not similarities:
                logger.warning(f"{wp.name} is not similar to any position")
                continue
            # Compute Softmax probabilities
            candidate_positions = list(similarities.keys())
            sim_values = [similarities[pos] for pos in candidate_positions]

            # Normalization
            exp_sims = [math.exp(s) for s in sim_values]
            sum_exp = sum(exp_sims)
            probabilities = [e / sum_exp if sum_exp > 0 else 1.0 / len(sim_values) for e in exp_sims]

            # Build dependency graph
            dependency_graph[wp] = {}
            for pos, raw, prob in zip(candidate_positions, sim_values, probabilities):
                dependency_graph[wp][pos] = {"jaccard_similarity": raw, "norm_weight": prob}

        logger.info("Field dependency graph generated")
        return dependency_graph

    def hyper_param(prob: float) -> bool:
        """ Hyper-parameter Bernoulli sampler """
        if not (0 <= prob <= 1):
            raise ValueError("Probability must be between 0 and 1 (inclusive).")
        return random.random() < prob

    def mutate_value_NoSource(
            self,
            api_position: ApiPosition,
            global_word_lib: WordLib,
            local_word_lib: LocalWordlib,
            possibility_to_choose_highlight: float = 1.0
    ) -> MutateValue:
        """
        Removed state-driven parameter provenance; instead, randomly samples from all corpora (no priority) to fill parameters.
        """
        candidates = []
        for lib in [self.target_word_lib, self.init_word_lib]:
            if lib is None:
                continue
            for word in lib.word_list():
                candidates.append(word.value)

        for _, pos_map in local_word_lib.items():
            if not pos_map:
                continue
            for _, words in pos_map.items():
                if words:
                    candidates.extend(words)
        if not candidates:
            return MutateValue(val="", is_ref=False)
        value = random.choice(candidates)
        return MutateValue(val=value, is_ref=False)

    def mutate_value(
            self,
            api_position: ApiPosition,
            global_word_lib: WordLib,
            local_word_lib: LocalWordlib,
            possibility_to_choose_highlight: float = 1.0
    ) -> MutateValue:
        """
        Return the mutated value. local_word_lib is a dict:
          { api_index: { Position: [fuzzword1, fuzzword2, ...], ... }, ... }
        """

        # 1) Select a dependent Position from the dependency graph probabilistically
        selected_pos = api_position
        deps = self.dependency_graph.get(api_position, {})
        name_lower = api_position.name.lower()
        csrf_flag = ("csrf" in name_lower) or ("token" in name_lower) or ("__c" in name_lower)
        if not deps:
            # logger.warning(f"No dependency found for {api_position.name}. Using self instead.")
            pass
        if deps and KeyDependencyModel.hyper_param(self.p_use_dependency):
            dep_positions = {pos: dep['jaccard_similarity'] for pos, dep in deps.items()}
            boost_coef = 500
            for pos in dep_positions:
                if isinstance(pos, ApiPosition) and csrf_flag:  # avoid reusing old csrf token values
                    continue
                # in_local: whether the current position exists in the local word library
                in_local = any(pos in pos_map and pos_map[pos] for pos_map in local_word_lib.values())
                # in_target: whether the position exists in the target word library
                in_target = bool(self.target_word_lib.position_map.get(pos, None))

                if (csrf_flag and in_local) or (not csrf_flag and (in_local or in_target)):
                    dep_positions[pos] = 1 * boost_coef  # boost dependency graph weight

            if not any(w > 0 for w in dep_positions.values()):
                dep_positions = {p: 1.0 for p in dep_positions}
            positions, probs = zip(*dep_positions.items())
            selected_pos = random.choices(positions, weights=probs, k=1)[0]

        # 2) If the selected Position exists in some local library(ies)
        if selected_pos is not None:
            # Find all local word library indices that contain this Position
            local_idxs = [
                idx for idx, pos_map in local_word_lib.items()
                if selected_pos in pos_map and pos_map[selected_pos]
            ]
            if local_idxs:
                # Prefer selecting from the local word library with higher probability
                if KeyDependencyModel.hyper_param(self.p_local_wordlib) or csrf_flag:
                    chosen_idx = random.choice(local_idxs)
                    # Return (API index, Position); the caller will further process it
                    return MutateValue(val="", is_ref=True, api_index=chosen_idx, pos=selected_pos)
                # Otherwise fall through to choose from target/global/initial libraries

        # 3) Randomly choose a library (target / initial / global) with weights; if empty, fall through to the next
        libs = [
            self.target_word_lib,  # target word library
            self.init_word_lib,  # initial (normal) word library
            global_word_lib,  # global word library
        ]
        # Higher weight for the target library; the other two share the remainder
        target_w = self.p_target_wordlib
        if target_w < 0 or target_w > 1:
            logger.error(f"p_target_wordlib must be between 0 and 1 (inclusive). using 0.8 instead.")
            target_w = 0.8
        other_w = (1 - target_w) / 2
        weights = [target_w, other_w, other_w]

        # Weighted random selection for the first candidate library
        first_idx = random.choices(range(3), weights=weights, k=1)[0]

        # Try up to three times: selected library → next → next
        for offset in range(3):
            idx = (first_idx + offset) % 3
            try:
                candidates = libs[idx].get_range(selected_pos)
            except Exception:
                candidates = []
            if candidates:
                group_0 = [candidate for candidate in candidates if candidate.weight == 0.0]
                group_1 = [candidate for candidate in candidates if candidate.weight != 0.0]
                # logger.debug(f"group 0: {group_0}, group 1: {group_1}")
                if not group_0 and group_1:
                    word = random.choice(group_1)
                    return MutateValue(val=word.value, is_ref=False)
                if not group_1 and group_0:
                    word = random.choice(group_0)
                    return MutateValue(val=word.value, is_ref=False)
                selected_group = random.choices(
                    population=[group_0, group_1],
                    weights=[1 - possibility_to_choose_highlight, possibility_to_choose_highlight],
                    k=1
                )[0]
                word = random.choice(selected_group)
                return MutateValue(val=word.value, is_ref=False)

        # 4) None of the libraries had candidates; return empty string ""
        logger.warning(f"No candidate value found for {api_position.name} in any wordlib.")
        return MutateValue(val="", is_ref=False)

    def mutate_key_value(
            self,
            father_seed: SeedInput,
            api_list: List[ApiNode],
            global_word_lib: WordLib,
    ) -> List[Dict[ApiPosition, MutateValue]]:
        """Mutate the last API of the seed."""
        api_num = len(api_list)
        value_dicts = father_seed.value_dicts.copy()
        if api_num > father_seed.api_num:
            value_dicts.append({})

        true_local_word_lib = {key: value for key, value in father_seed.local_wordlib.items() if key < api_num}
        api_node = api_list[-1]
        api_positions = api_node.positions

        value_dict: Dict[ApiPosition, MutateValue] = {}
        for api_position in api_positions:
            if api_position.is_required == False:
                if KeyDependencyModel.hyper_param(self.p_optional_pos):
                    continue
            mutate_value = self.mutate_value(api_position, global_word_lib, true_local_word_lib)
            # mutate_value = self.mutate_value_NoSource(api_position, global_word_lib, true_local_word_lib)
            value_dict[api_position] = mutate_value
        value_dicts[-1] = value_dict

        return value_dicts

    def get_position_satisfiability(
            self,
            local_word_lib: LocalWordlib,
            global_word_lib: WordLib = None,
    ) -> Dict[ApiPosition, float]:
        """
        For each api_position in self.all_api_positions, compute its satisfiability score, returning {ApiPosition: float}
        """
        # Tunable parameters
        local_target_coef = 1.0
        init_coef = 0.2

        result: Dict[ApiPosition, float] = dict()

        for api_pos in self.all_api_positions:
            value = 0.0
            deps = self.dependency_graph.get(api_pos, {})

            if not deps:
                # No dependencies; only check the initial word library
                if api_pos in self.init_word_lib.position_map:
                    value = 1.0
                else:
                    value = 0.0
            else:
                dep_positions = {pos: dep['jaccard_similarity'] for pos, dep in deps.items()}
                dep_value = 0.0
                for dep_pos, jaccardWeight in dep_positions.items():
                    # in_local: hit in any local_word_lib is sufficient
                    in_local = any(
                        dep_pos in pos_map and pos_map[dep_pos]
                        for pos_map in local_word_lib.values()
                    )
                    # in_target: whether the target library contains the dependency
                    in_target = bool(self.target_word_lib.position_map.get(dep_pos, None))
                    # in_init: hit in the initial word library
                    in_init = dep_pos in self.init_word_lib.position_map

                    if in_local or in_target:
                        dep_value = jaccardWeight * local_target_coef
                    elif in_init:
                        dep_value = jaccardWeight * init_coef

                    value = max(value, dep_value)

            result[api_pos] = min(1.0, value)
        return result

    def short_node_label(self, pos):
        if hasattr(pos, 'table_name') and hasattr(pos, 'col_name'):
            tbl, col = pos.table_name, pos.col_name
            tbl = tbl if len(tbl) <= 12 else tbl[:10] + "…"
            col = col if len(col) <= 14 else col[:12] + "…"
            return f"{tbl}.{col}"
        elif hasattr(pos, 'file_path'):
            base = pos.file_path.split('/')[-1]
            mark = '[content]' if pos.is_content else '[name]'
            return f"{base}{mark}"
        elif hasattr(pos, 'type') and hasattr(pos, 'where'):
            where = pos.where
            w = where if len(where) < 18 else "…" + where[-14:]
            return f"{pos.type} Response@{w}"
        elif hasattr(pos, 'name') and hasattr(pos, 'whose'):
            whose = pos.whose
            try:
                if isinstance(whose, bytes):
                    try:
                        obj = msgspec.msgpack.decode(whose)
                        method = obj.get('method') or obj.get('METHOD') or obj.get('Method')
                        path = obj.get('path') or obj.get('PATH') or obj.get('Path')
                        if isinstance(method, bytes): method = method.decode('utf-8', 'ignore')
                        if isinstance(path, bytes): path = path.decode('utf-8', 'ignore')
                        if method and path:
                            return f"{pos.name}({method} {path})"
                    except Exception:
                        pass
            except Exception:
                pass
            sid = whose.hex()[:8] if isinstance(whose, bytes) else str(whose)[:8]
            return f"{pos.name}({sid})"
        elif hasattr(pos, 'name'):
            return pos.name
        return str(pos)

    def position_type(self, pos):
        """
        Return one of 'api','table','file','resp','other'
        """
        if hasattr(pos, "name") and hasattr(pos, "whose"):
            return "api"
        if hasattr(pos, "table_name") and hasattr(pos, "col_name"):
            return "table"
        if hasattr(pos, "file_path"):
            return "file"
        if hasattr(pos, "type") and hasattr(pos, "where"):
            return "resp"
        return "other"

    def output_dependency_html(self, output_file: str = "key_dependency_graph.html"):
        dependency_graph = self.dependency_graph
        html_parts = ["""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Field Dependency Graph</title>
<style>
body {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #faf7f3; margin: 0; padding: 0;
}
.mainbox {
    max-width: 1200px;
    margin: 36px auto 50px auto;
    background: #fff;
    padding: 38px 52px 23px 49px;
    border-radius: 16px;
    box-shadow: 0 4px 24px #efeae4;
}
.legend-box {
    margin-bottom: 32px;
    padding: 13px 20px 10px 18px;
    background: #f6f6f8;
    border-radius: 8px;
    border: 1.3px solid #e1e4ec;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    font-size: 1em;
    gap: 18px 22px;
}
.legend-label {
    display: flex; align-items: center; margin-right: 12px; min-width: 135px;
    font-size: 1.01em;
}
.legend-color {
    display: inline-block; width: 27px; height: 19px; border-radius: 5px;
    margin-right: 9px; vertical-align: middle; border: 1.2px solid #aaa;
}
.leg-api   { background: #eaf4ff; border-color: #7bb8ee;}
.leg-table { background: #faefe1; border-color: #eaca8a;}
.leg-file  { background: #edf8ea; border-color: #93c895;}
.leg-resp  { background: #f8e8f5; border-color: #ec9ae2;}
.leg-other { background: #eee;    border-color: #bbb; }
/* -------------------------------------- */
.api-block {
    margin-bottom: 28px; border-left: 5px solid #4a90e2; padding-left: 23px;
}
.api-title {
    color: #274472; font-size: 1.13em; font-weight: bold; margin-bottom: 10px; letter-spacing: 0.5px;
}
.dep-list {
    display: flex;
    flex-wrap: wrap;
    gap: 18px 18px;
    font-size: 1em;
    margin-left: 0.5px;
}
.dep-item { display: flex; align-items: center;
    flex: 1 0 17%; max-width: 22%; min-width: 180px;
    box-sizing: border-box; text-align: left;
    padding: 7px 7px 7px 13px;
    border-radius: 7px; margin-bottom: 8px;
    border: 1px solid #dee3ef;
    color: #133057; cursor: help; position: relative;
    transition: box-shadow 0.13s;
    word-break: break-all; font-size: 1em;
    background: #f5f8ff;
}
/* API field dependency block */
.dep-type-api   { background: #eaf4ff; border-color: #7bb8ee; color:#183975;}
/* Database table field */
.dep-type-table { background: #faefe1; border-color: #e9cb7a; color:#614300;}
/* File field */
.dep-type-file  { background: #edf8ea; border-color: #93c895; color:#285629;}
/* Response body (respond) */
.dep-type-resp  { background: #f8e8f5; border-color: #ec9ae2; color:#a3117e;}
/* Other fields */
.dep-type-other { background: #eee;    border-color: #bbb;    color:#444;}
.dep-item:hover {
    background: #e9f8ee;
    box-shadow: 0 0 7px #a3e2ca90;
    z-index: 3;
}
.dep-label-part {
    flex: 1; padding-right:7px;
    overflow-wrap:break-word; word-break: break-all;
}
.dep-sep {
    width: 1.5px; background: #b9bfd1;
    height: 70%; margin: 0 10px 0 2px;
    border-radius: 1.5px;
    min-width:1px; max-width:2px; display: inline-block;
}
/* Compact vertical alignment for weight blocks */
.dep-weights-block {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    justify-content: center;
    min-width: 56px; max-width: 70px;
    text-align: center;
}
.dep-weight {
    display: flex;
    align-items: center;  /* vertically centered */
    justify-content: center; /* horizontally centered */
    color: #fff;
    background: #6ca01b;
    font-weight: bold;
    border-radius: 9px;
    padding: 0.4em 0;   /* tighter spacing */
    margin-bottom: 2px;
    font-size: 1.08em;
    letter-spacing:1px;
    min-width:51px; max-width:65px;
    box-sizing: border-box;
    height: 28px;
    user-select: all;
}
.dep-weight.low  { background: #aaaaad; }
.dep-weight.mid  { background: #f9ac2a; }
.dep-weight.high { background: #e8503a;}
.dep-jaccard {
    display: flex;
    align-items: center; justify-content: center;
    color: #35547b;
    background: #e8eef9;
    border-radius: 6px;
    font-size: 0.93em;
    padding: 0.28em 0;
    min-width:51px; max-width:65px;
    height:22px;
    box-sizing: border-box;
    font-family: consolas, monospace;
    user-select: all;
}
.dep-tip {
    display: none;
    position: absolute;
    left: 50%;
    top: 114%;
    transform: translateX(-50%);
    background: #234; color: #fff; font-size: 1.03em; line-height: 1.28em;
    box-shadow: 0 2px 10px #99a; padding: 11px 23px 11px 18px;
    border-radius: 10px; min-width: 330px; max-width: 600px;
    word-break: break-all; z-index: 10; white-space: pre-line;
    border: 1.5px solid #5a77ad;
}
.dep-item:hover .dep-tip { display: block; }
</style>
</head>
<body>
<div class="mainbox">
<h2 style="margin:2px 0 20px 3px;color:#316;">Field Dependency Graph</h2>

<!-- Legend -->
<div class="legend-box">
    <span class="legend-label"><span class="legend-color leg-api"></span> ApiPosition</span>
    <span class="legend-label"><span class="legend-color leg-table"></span> TablePosition</span>
    <span class="legend-label"><span class="legend-color leg-file"></span> FilePosition</span>
    <span class="legend-label"><span class="legend-color leg-resp"></span> ResponsePosition</span>
    <span class="legend-label"><span class="legend-color leg-other"></span> Other</span>
    <span class="legend-label" style="min-width:260px;gap:28px;padding-left:8px;">
        <span style="display:flex;align-items:center;gap:7px;">
            <span class="dep-weight mid" style="min-width:44px;height:22px;display:flex;align-items:center;justify-content:center;padding:0;margin-right:5px;font-size:0.98em;">0.512</span>
            <span style="font-size:0.98em;color:#444;">Normalized weight</span>
        </span>
        <span style="display:flex;align-items:center;gap:7px;">
            <span class="dep-jaccard" style="min-width:44px;height:17px;display:flex;align-items:center;justify-content:center;padding:0 2px;margin-right:5px;font-size:0.95em;">0.678</span>
            <span style="font-size:0.97em;color:#444;">Jaccard similarity</span>
        </span>
    </span>
</div>
"""]

        # Sort main field blocks
        src_list = [
            src for src in dependency_graph
            if hasattr(src, 'name') and hasattr(src, 'whose')
        ]
        src_list.sort(key=lambda x: self.short_node_label(x))

        for src in src_list:
            src_label = self.short_node_label(src)
            deps = dependency_graph[src]
            if not deps:
                continue
            # Sort by norm_weight in descending order
            sorted_deps = sorted(
                deps.items(), key=lambda x: -x[1].get("norm_weight", 0.0)
            )

            dep_chunks = []
            for dst, d in sorted_deps:
                prob = d.get("norm_weight", 0.0)
                raw = d.get("jaccard_similarity", None)
                prob_disp = f"{prob:.3f}"
                raw_disp = f"{raw:.3f}" if raw is not None else "-"
                dst_label = self.short_node_label(dst)
                if prob >= 0.7:
                    wcls = "dep-weight high"
                elif prob >= 0.3:
                    wcls = "dep-weight mid"
                else:
                    wcls = "dep-weight low"
                dtype = self.position_type(dst)
                dep_chunks.append(
                    f'''<span class="dep-item dep-type-{dtype}" tabindex="0">
                          <span class="dep-label-part">{dst_label}</span>
                          <span class="dep-sep"></span>
                          <span class="dep-weights-block">
                              <span class="{wcls}">{prob_disp}</span>
                              <span class="dep-jaccard">{raw_disp}</span>
                          </span>
                          <span class="dep-tip">{str(dst).replace('<', '&lt;').replace('>', '&gt;')}</span>
                    </span>'''
                )

            html_parts.append(
                f'<div class="api-block">'
                f'  <div class="api-title">{src_label}</div>'
                f'  <div class="dep-list">{"".join(dep_chunks)}</div>'
                f'</div>'
            )

        html_parts.append("</div></body></html>")

        content = "\n".join(html_parts)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Field dependency graph saved to: {output_file}")


