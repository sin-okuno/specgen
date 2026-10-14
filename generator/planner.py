"""Decide which Angular files a validated Screen Model produces."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from generator.errors import GeneratorError
from generator.naming import (
    IDENT,
    action_label,
    api_type_stem,
    camel,
    field_decl,
    file_slug,
    member,
    pascal,
    prop,
    screen_stem,
)
from generator.naming import access as ts_access
from generator.spec_rules import (
    BODY_METHODS,
    SUPPORTED_AREAS,
    SUPPORTED_LOCATIONS,
    SUPPORTED_MAPPINGS,
    SUPPORTED_METHODS,
    SUPPORTED_OPERATIONS,
)
from generator.state_tree import (
    SBranch,
    SLeaf,
    insert_state,
    iter_leaves,
    render_prop_case,
    render_state_initial,
    render_state_type,
    render_success_case,
)
from generator.types import TypeMapper, split_type

_PATH_TOKEN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_AREA_ID = re.compile(r"[A-Z]+-\d+\Z")
_ITEM_SOURCE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*)\[\]\.([A-Za-z_][A-Za-z0-9_]*)$")
_MAX_LENGTH = re.compile(r"maxLength:(\d+)\Z")
_OPTIONS = re.compile(r"options:([A-Za-z0-9-]+)\Z")
_ROUTE_ASSIGN = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=route\.([A-Za-z_][A-Za-z0-9_]*)\Z")
_SEARCH_OPS = frozenset({"VALIDATE", "RESET_PAGE", "APPLY_QUERY", "CALL_API", "NAVIGATE"})
_HTTP = {
    "GET": "get",
    "POST": "post",
    "PUT": "put",
    "PATCH": "patch",
    "DELETE": "delete",
}


@dataclass(frozen=True)
class PlannedFile:
    relative_path: str
    template: str
    depends: tuple[str, ...]
    context: dict[str, Any]


@dataclass(frozen=True)
class GenerationPlan:
    screen_id: str
    screen_name: str
    files: tuple[PlannedFile, ...]


def build_plan(document: dict[str, Any]) -> GenerationPlan:
    model = document["model"]
    meta = document["metadata"]
    screen_id = str(meta["screen_id"])
    stem = screen_stem(str(meta["screen_name"]))
    prefix = stem
    slug = file_slug(stem)
    feature = camel(stem)
    mapper = TypeMapper(
        [row["type_name"] for row in model["named_type_catalog"]],
        model["named_type_fields"],
    )
    _reject_unsupported(model, mapper)
    header = _header(document)
    state = _state_tree(model)
    apis = _api_views(model, mapper)
    areas = _area_views(prefix, slug, model["areas"])
    rules = _list_rules(model, mapper)
    _attach_columns(areas, model, feature, slug, mapper, str(meta["url"]), apis)
    _attach_facts(areas, model, feature, slug, mapper)
    _attach_search(areas, model, apis, prefix, slug, header, mapper, rules, str(meta["url"]))
    init = _init_plan(model, apis, str(meta["url"]), mapper)
    init_calls = init["calls"]
    init_routes = init["routes"]
    initialize = f"initialize{prefix}" if init_calls else ""
    models_path = f"{slug}/models/{slug}.models.ts"
    state_path = f"{slug}/store/{slug}.state.ts"
    actions_path = f"{slug}/store/{slug}.actions.ts"
    reducer_path = f"{slug}/store/{slug}.reducer.ts"
    effects_path = f"{slug}/store/{slug}.effects.ts"
    selectors_path = f"{slug}/store/{slug}.selectors.ts"
    service_path = f"{slug}/services/{slug}-api.service.ts"
    steps_path = f"{slug}/{slug}.steps.ts"
    module_path = f"{slug}/{slug}.module.ts"
    area_files = _area_files(slug, areas)
    component_ts = tuple(path for path, _html, _area in area_files)

    files = [
        PlannedFile(
            models_path,
            "models.ts.j2",
            (),
            _models_context(header, feature, mapper, apis, model),
        ),
        PlannedFile(
            state_path,
            "state.ts.j2",
            (models_path,),
            {
                "header": header,
                "slug": slug,
                "feature_key": feature,
                "feature_literal": _js(feature),
                "class_prefix": prefix,
                "model_imports": _state_imports(state, mapper),
                "state_body": render_state_type(state, mapper, 0),
                "initial_body": render_state_initial(
                    state,
                    mapper,
                    0,
                    None if rules is None else rules["overrides"],
                ),
                "spec_initial": rules is not None,
            },
        ),
        PlannedFile(
            actions_path,
            "actions.ts.j2",
            (models_path,),
            _actions_context(
                header,
                slug,
                apis,
                action_label(stem),
                initialize,
                rules,
                init_routes,
            ),
        ),
        PlannedFile(
            reducer_path,
            "reducer.ts.j2",
            (actions_path, state_path),
            _reducer_context(header, slug, feature, prefix, apis, rules),
        ),
        PlannedFile(
            effects_path,
            "effects.ts.j2",
            (actions_path, service_path),
            _effects_context(
                header,
                slug,
                prefix,
                apis,
                initialize,
                init_calls,
                _success_navigations(areas),
                init_routes,
                not init_routes or init["reads_state"],
                _form_fills(areas, model, apis),
                _mark_pristine(areas, model, apis, str(meta["url"]), mapper),
            ),
        ),
        PlannedFile(
            selectors_path,
            "selectors.ts.j2",
            (state_path,),
            _selector_context(header, slug, feature, prefix, state),
        ),
        PlannedFile(
            service_path,
            "api.service.ts.j2",
            (models_path,),
            _service_context(header, slug, prefix, apis),
        ),
        PlannedFile(
            steps_path,
            "steps.ts.j2",
            (),
            _steps_context(header, feature, meta, model),
        ),
    ]
    emitted_form = False
    for path, html_path, area in area_files:
        if area["form_context"] and not emitted_form:
            files.append(
                PlannedFile(
                    str(area["form_path"]),
                    "query.form.ts.j2",
                    (),
                    area["form_context"],
                )
            )
            emitted_form = True
        form_depends = (str(area["form_path"]),) if area["form_class"] else ()
        files.append(
            PlannedFile(
                path,
                "component.ts.j2",
                form_depends,
                {"header": header, "area": area, "feature_key": feature, "slug": slug},
            )
        )
        files.append(
            PlannedFile(
                html_path,
                "component.html.j2",
                (),
                {"area": area},
            )
        )
    screen_ts = f"{slug}/{slug}.component.ts"
    screen_html = f"{slug}/{slug}.component.html"
    files.append(
        PlannedFile(
            screen_ts,
            "screen.component.ts.j2",
            (actions_path,) if initialize else (),
            {
                "header": header,
                "class_name": f"{prefix}ScreenComponent",
                "selector": f"app-{slug}",
                "file_stem": slug,
                "areas": areas,
                "initialize": initialize,
                "routes": init_routes,
                "slug": slug,
            },
        )
    )
    files.append(
        PlannedFile(
            screen_html,
            "screen.component.html.j2",
            (),
            {"areas": areas},
        )
    )
    files.append(
        PlannedFile(
            module_path,
            "module.ts.j2",
            (
                *component_ts,
                *(str(area["form_path"]) for area in areas if area["form_context"]),
                screen_ts,
                state_path,
                reducer_path,
                effects_path,
                service_path,
            ),
            _module_context(header, slug, feature, prefix, areas),
        )
    )
    return GenerationPlan(screen_id, str(meta["screen_name"]), tuple(files))


def _header(document: dict[str, Any]) -> str:
    source = str(document["source"])
    screen_name = str(document["metadata"]["screen_name"])
    if "\n" in source or "\n" in screen_name:
        raise GeneratorError("UNSUPPORTED_NAME", "header")
    return "\n".join(
        (
            "// Generated from Screen Model schema 0.3. Phase 1 scaffold.",
            f"// screen: {screen_name}",
            f"// source: {source}",
        )
    )


def _reject_unsupported(model: dict[str, Any], mapper: TypeMapper) -> None:
    for row in model["named_type_fields"]:
        mapper.ts(row["data_type"], nullable=row["nullable"] == "Yes")
    for key in ("inputs", "displays", "requests", "responses", "route_parameters"):
        for row in model[key]:
            mapper.ts(row["data_type"])
    for row in model["state_types"]:
        mapper.ts(row["data_type"], nullable=row["nullable"] == "Yes")
    for row in [*model["initialization"], *model["event_steps"]]:
        if row["operation"] not in SUPPORTED_OPERATIONS:
            raise GeneratorError("UNSUPPORTED_OPERATION", str(row["operation"]))
    for row in model["apis"]:
        if row["method"] not in SUPPORTED_METHODS:
            raise GeneratorError("UNSUPPORTED_METHOD", f"{row['api_id']} {row['method']}")
    for row in model["requests"]:
        if row["location"] not in SUPPORTED_LOCATIONS:
            raise GeneratorError("UNSUPPORTED_LOCATION", f"{row['api_id']} {row['location']}")
    for row in model["response_mappings"]:
        if row["mapping_mode"] not in SUPPORTED_MAPPINGS:
            raise GeneratorError(
                "UNSUPPORTED_MAPPING",
                f"{row['api_id']} {row['mapping_mode']}",
            )
    for row in model["areas"]:
        if row["area_type"] not in SUPPORTED_AREAS:
            raise GeneratorError("UNSUPPORTED_AREA", str(row["area_type"]))
        if not _AREA_ID.fullmatch(str(row["area_id"])):
            raise GeneratorError("UNSUPPORTED_AREA", str(row["area_id"]))


def _state_imports(state: SBranch, mapper: TypeMapper) -> list[str]:
    names: list[str] = []
    for path in iter_leaves(state):
        node: SBranch | SLeaf = state
        for part in path:
            if not isinstance(node, SBranch):
                break
            node = node.fields[part]
        if not isinstance(node, SLeaf):
            continue
        base, _is_array = split_type(node.data_type)
        if base not in mapper.names:
            continue
        rendered = pascal(base)
        if rendered not in names:
            names.append(rendered)
    return names


def _state_tree(model: dict[str, Any]) -> SBranch:
    root = SBranch()
    for row in model["state_types"]:
        insert_state(
            root,
            str(row["state_path"]),
            str(row["data_type"]),
            nullable=row["nullable"] == "Yes",
        )
    return root


def _api_views(model: dict[str, Any], mapper: TypeMapper) -> list[dict[str, Any]]:
    requests: dict[str, list[dict[str, Any]]] = {}
    responses: dict[str, list[dict[str, Any]]] = {}
    mappings: dict[str, list[dict[str, Any]]] = {}
    for row in model["requests"]:
        requests.setdefault(str(row["api_id"]), []).append(row)
    for row in model["responses"]:
        responses.setdefault(str(row["api_id"]), []).append(row)
    for row in model["response_mappings"]:
        mappings.setdefault(str(row["api_id"]), []).append(row)
    stems: set[str] = set()
    views: list[dict[str, Any]] = []
    for api in model["apis"]:
        api_id = str(api["api_id"])
        params = requests.get(api_id, [])
        _unique_params(api_id, params)
        path_params = [row for row in params if row["location"] == "PATH"]
        query_params = [row for row in params if row["location"] == "QUERY"]
        body_params = [row for row in params if row["location"] == "BODY"]
        method = str(api["method"])
        endpoint = str(api["endpoint"])
        purpose = str(api["purpose"])
        if body_params and method not in BODY_METHODS:
            raise GeneratorError("UNSUPPORTED_LOCATION", f"{api_id} BODY on {method}")
        _check_path(api_id, endpoint, path_params)
        stem = api_type_stem(endpoint, purpose)
        if stem in stems:
            stem = f"{stem}{pascal(method)}"
        if stem in stems:
            raise GeneratorError("UNSUPPORTED_NAME", f"{api_id} {purpose}")
        stems.add(stem)
        base = camel(stem)
        response_name = f"{stem}Response"
        request_name = f"{stem}Request" if params else ""
        views.append(
            {
                "api_id": api_id,
                "method": method,
                "http": _HTTP[method],
                "endpoint": endpoint,
                "purpose": purpose,
                "type_stem": stem,
                "action_label": action_label(stem),
                "method_name": f"{_HTTP[method]}{stem}",
                "action": base,
                "success": f"{base}Success",
                "failure": f"{base}Failure",
                "effect": f"{base}$",
                "request_name": request_name,
                "response_name": response_name,
                "has_request": bool(params),
                "params": [_param_view(row, mapper) for row in params],
                "query_params": [_param_view(row, mapper) for row in query_params],
                "body_params": [_param_view(row, mapper) for row in body_params],
                "path_params": [_param_view(row, mapper) for row in path_params],
                "response_fields": [
                    _response_field(row, mapper) for row in responses.get(api_id, [])
                ],
                "updates": _updates(
                    [
                        row
                        for row in mappings.get(api_id, [])
                        if not str(row["destination"]).startswith("input.")
                    ]
                ),
            }
        )
    return views


def _param_view(row: dict[str, Any], mapper: TypeMapper) -> dict[str, Any]:
    name = str(row["parameter"])
    optional = row["required"] == "No"
    source = str(row["source"])
    if "\n" in source or "*/" in source:
        raise GeneratorError("UNSUPPORTED_REQUEST", name)
    return {
        "name": name,
        "member": member(name),
        "optional": optional,
        "decl": field_decl(name, mapper.ts(str(row["data_type"])), optional=optional),
        "source": source,
        "comment": f"source: {source}; location: {row['location']}",
    }


def _response_field(row: dict[str, Any], mapper: TypeMapper) -> str:
    return field_decl(
        str(row["field"]),
        mapper.ts(str(row["data_type"]), nullable=row["nullable"] == "Yes"),
        optional=row["required"] == "No",
    )


def _updates(rows: list[dict[str, Any]]) -> list[tuple[list[str], str]]:
    updates: list[tuple[list[str], str]] = []
    for row in rows:
        destination = str(row["destination"])
        segments = destination.split(".")
        if not segments or any(part == "" for part in segments):
            raise GeneratorError("UNSUPPORTED_STATE", destination)
        updates.append((segments, ts_access("action.body", str(row["response_field"]))))
    return updates


def _unique_params(api_id: str, rows: list[dict[str, Any]]) -> None:
    names = [str(row["parameter"]) for row in rows]
    if len(names) != len(set(names)):
        raise GeneratorError("UNSUPPORTED_REQUEST", api_id)


def _check_path(api_id: str, endpoint: str, path_params: list[dict[str, Any]]) -> None:
    tokens = _PATH_TOKEN.findall(endpoint)
    names = [str(row["parameter"]) for row in path_params]
    if any(row["required"] == "No" for row in path_params):
        raise GeneratorError("UNSUPPORTED_PATH", f"{api_id} の PATH は必須です")
    if sorted(tokens) != sorted(names) or len(tokens) != len(set(tokens)):
        raise GeneratorError("UNSUPPORTED_PATH", f"{api_id} {endpoint}")
    if _PATH_TOKEN.sub("", endpoint).find("{") != -1 or "}" in _PATH_TOKEN.sub("", endpoint):
        raise GeneratorError("UNSUPPORTED_PATH", f"{api_id} {endpoint}")


def _area_views(prefix: str, slug: str, areas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, int] = {}
    views: list[dict[str, Any]] = []
    for area in areas:
        area_type = str(area["area_type"])
        area_id = str(area["area_id"])
        area_name = str(area["area_name"])
        if "\n" in area_name or "*/" in area_name:
            raise GeneratorError("UNSUPPORTED_AREA", area_id)
        index = seen.get(area_type, 0) + 1
        seen[area_type] = index
        folder = area_type.lower()
        class_name = prefix + pascal(area_type)
        if index > 1:
            folder = f"{folder}-{index}"
            class_name = f"{class_name}{index}"
        stem = f"{slug}-{folder}"
        views.append(
            {
                "area_id": area_id,
                "area_type": area_type,
                "area_name": area_name,
                "folder": folder,
                "class_name": f"{class_name}Component",
                "selector": f"app-{stem}",
                "file_stem": stem,
            }
        )
    return views


def _area_files(
    slug: str, areas: list[dict[str, Any]]
) -> list[tuple[str, str, dict[str, Any]]]:
    files: list[tuple[str, str, dict[str, Any]]] = []
    for area in areas:
        base = f"{slug}/{area['folder']}/{area['file_stem']}.component"
        files.append((f"{base}.ts", f"{base}.html", area))
    return files


def _attach_columns(
    areas: list[dict[str, Any]],
    model: dict[str, Any],
    feature: str,
    slug: str,
    mapper: TypeMapper,
    url: str,
    apis: list[dict[str, Any]],
) -> None:
    state_paths = {str(row["state_path"]) for row in model["state_types"]}
    codes = model["codes"]
    for area in areas:
        columns: list[dict[str, str]] = []
        collection = ""
        for display in model["displays"]:
            if display["area_id"] != area["area_id"]:
                continue
            match = _ITEM_SOURCE.fullmatch(str(display["source"]))
            if not match:
                continue
            path, field = match.group(1), match.group(2)
            if path not in state_paths:
                continue
            if collection and collection != path:
                raise GeneratorError("UNSUPPORTED_AREA", str(area["area_id"]))
            collection = path
            label = str(display["label"])
            if "\n" in label or "<" in label or "{{" in label:
                raise GeneratorError("UNSUPPORTED_AREA", str(area["area_id"]))
            fmt = str(display["display_format"])
            code_id = fmt.split(":", 1)[1] if fmt.startswith("CODE:") else ""
            columns.append(
                {
                    "label": label,
                    "field": field,
                    "member": member(field),
                    "empty": str(display["empty_display"]),
                    "code_id": code_id,
                    "data_type": str(display["data_type"]),
                }
            )
        area["columns"] = columns
        area["empty"] = None
        area["row_nav"] = None
        area["table"] = ""
        area["items_selector"] = ""
        area["items_type"] = ""
        area["model_import"] = ""
        area["has_code"] = False
        area["code_groups"] = []
        if not columns:
            continue
        used = {column["code_id"] for column in columns if column["code_id"]}
        area["code_groups"] = _code_groups(codes, used)
        area["has_code"] = bool(used)
        area["items_selector"] = "select" + "".join(pascal(part) for part in collection.split("."))
        area["items_type"] = _state_type_name(model, mapper, collection)
        area["model_import"] = _model_import(
            feature,
            slug,
            _named_imports(model, mapper, collection),
            bool(area["code_groups"]),
        )
        track = "item.id" if any(column["field"] == "id" for column in columns) else "$index"
        area["row_nav"] = _row_nav(url, columns)
        area["empty"] = _empty_result(model, apis, collection)
        area["table"] = _render_table(
            str(area["area_type"]),
            columns,
            track,
            area["row_nav"] is not None,
            None if area["empty"] is None else str(area["empty"]["message"]),
        )


def _attach_facts(
    areas: list[dict[str, Any]],
    model: dict[str, Any],
    feature: str,
    slug: str,
    mapper: TypeMapper,
) -> None:
    state_rows = {str(row["state_path"]): row for row in model["state_types"]}
    codes = model["codes"]
    known_codes = {str(row["code_id"]) for row in codes}
    for area in areas:
        area["facts"] = None
        if area["columns"] or str(area["area_type"]) != "DETAIL":
            continue
        facts: list[dict[str, str]] = []
        root = ""
        for display in model["displays"]:
            if display["area_id"] != area["area_id"]:
                continue
            located = _fact_source(str(display["source"]), state_rows)
            if located is None:
                continue
            path, relative, data_type = located
            if root and root != path:
                raise GeneratorError("UNSUPPORTED_AREA", str(area["area_id"]))
            root = path
            label = str(display["label"])
            field_id = str(display["field_id"])
            empty = str(display["empty_display"])
            if (
                not IDENT.fullmatch(field_id)
                or "\n" in label
                or "<" in label
                or "{{" in label
                or "\n" in empty
                or "<" in empty
            ):
                raise GeneratorError("UNSUPPORTED_AREA", str(area["area_id"]))
            fmt = str(display["display_format"])
            code_id = ""
            if fmt.startswith("CODE:"):
                code_id = fmt.split(":", 1)[1]
                if code_id not in known_codes:
                    raise GeneratorError("UNSUPPORTED_AREA", code_id)
            elif fmt not in {"TEXT", "NUMBER"}:
                raise GeneratorError("UNSUPPORTED_AREA", fmt)
            facts.append(
                {
                    "id": field_id,
                    "label": label,
                    "access": _relative_access(mapper, data_type, relative),
                    "empty": empty,
                    "format": "CODE" if code_id else fmt,
                    "code_id": code_id,
                }
            )
        if not facts or not root:
            continue
        signal = root.split(".")[-1]
        if not IDENT.fullmatch(signal):
            raise GeneratorError("UNSUPPORTED_AREA", root)
        used = {fact["code_id"] for fact in facts if fact["code_id"]}
        area["facts"] = {
            "signal": signal,
            "selector": "select" + "".join(pascal(part) for part in root.split(".")),
            "type_name": _state_type_name(model, mapper, root),
            "model_import": _model_import(
                feature,
                slug,
                _named_imports(model, mapper, root),
                bool(used),
            ),
            "has_code": bool(used),
            "code_groups": _code_groups(codes, used),
        }
        area["table"] = _render_facts(str(area["area_type"]), signal, facts)


def _fact_source(
    source: str,
    state_rows: dict[str, dict[str, Any]],
) -> tuple[str, str, str] | None:
    best = ""
    for path in state_rows:
        if source == path or source.startswith(path + "."):
            if len(path) > len(best):
                best = path
    if not best:
        return None
    relative = "" if source == best else source[len(best) + 1 :]
    return best, relative, str(state_rows[best]["data_type"])


def _relative_access(mapper: TypeMapper, data_type: str, relative: str) -> str:
    if not relative:
        return ""
    current = data_type
    parts: list[str] = []
    for segment in relative.split("."):
        if not IDENT.fullmatch(segment):
            raise GeneratorError("UNSUPPORTED_AREA", relative)
        base, is_array = split_type(current)
        if is_array or base not in mapper.names:
            raise GeneratorError("UNSUPPORTED_AREA", relative)
        row = next(
            (item for item in mapper.fields[base] if str(item["field"]) == segment),
            None,
        )
        if row is None:
            raise GeneratorError("UNSUPPORTED_AREA", relative)
        parts.append(member(segment))
        current = str(row["data_type"])
    return "".join(parts)


def _render_facts(area_type: str, signal: str, facts: list[dict[str, str]]) -> str:
    lines = [
        f'<section data-area-type="{_html(area_type)}">',
        "  <dl>",
    ]
    for fact in facts:
        label = _html(fact["label"])
        field_id = fact["id"]
        access = f"{signal}(){fact['access']}"
        empty = _js(fact["empty"])
        if fact["format"] == "CODE":
            expr = f"{{{{ codeLabel({_js(fact['code_id'])}, {access}, {empty}) }}}}"
        elif fact["format"] == "NUMBER":
            expr = f"{{{{ {access} == null ? {empty} : {access} }}}}"
        else:
            expr = f'{{{{ {access} == null || {access} === "" ? {empty} : {access} }}}}'
        lines.append(f'    <div id="{field_id}">')
        lines.append(f"      <dt>{label}</dt>")
        lines.append(f"      <dd>{expr}</dd>")
        lines.append("    </div>")
    lines.extend(["  </dl>", "</section>"])
    return "\n".join(lines)


def _list_rules(model: dict[str, Any], mapper: TypeMapper) -> dict[str, Any] | None:
    rows = model["screen_specific"]["11.1"]
    if not rows:
        return None
    values = {str(row["item"]): str(row["value"]) for row in rows}
    required = (
        "ページング方式",
        "初期ページ",
        "初期表示件数",
        "表示件数候補",
        "初期ソート",
        "複数列ソート",
        "検索時ページ初期化",
    )
    if any(item not in values for item in required):
        raise GeneratorError("UNSUPPORTED_LIST", "11.1")
    if values["ページング方式"] != "SERVER" or values["複数列ソート"] != "No":
        raise GeneratorError("UNSUPPORTED_LIST", "11.1")
    if values["検索時ページ初期化"] not in {"Yes", "No"}:
        raise GeneratorError("UNSUPPORTED_LIST", "11.1")
    page = _integer_literal(values["初期ページ"], "初期ページ")
    page_size = _integer_literal(values["初期表示件数"], "初期表示件数")
    sizes = [
        _integer_literal(item.strip(), "表示件数候補")
        for item in values["表示件数候補"].split(",")
        if item.strip()
    ]
    if page_size not in sizes:
        raise GeneratorError("UNSUPPORTED_LIST", "初期表示件数")
    ordering = values["初期ソート"]
    if "\n" in ordering:
        raise GeneratorError("UNSUPPORTED_LIST", "初期ソート")
    bindings = (
        ("pagination.page", page, "integer"),
        ("pagination.pageSize", page_size, "integer"),
        ("sort.ordering", _js(ordering), "string"),
    )
    state_rows = {str(row["state_path"]): row for row in model["state_types"]}
    setters: list[dict[str, str]] = []
    overrides: dict[str, str] = {}
    resets: dict[str, dict[str, str]] = {}
    for path, literal, data_type in bindings:
        row = state_rows.get(path)
        if row is None or str(row["data_type"]) != data_type or row["nullable"] == "Yes":
            raise GeneratorError("UNSUPPORTED_LIST", path)
        mapper.ts(data_type)
        prop_name = path.split(".")[-1]
        prop_type = mapper.ts(data_type)
        setter = "set" + "".join(pascal(part) for part in path.split("."))
        setters.append(
            {
                "path": path,
                "name": setter,
                "prop": prop_name,
                "type": prop_type,
                "literal": literal,
                "label": "Set " + action_label("".join(pascal(part) for part in path.split("."))),
            }
        )
        overrides[path] = literal
        if path == "pagination.page":
            resets[path] = {
                "literal": literal,
                "name": setter,
                "dispatch": f"this.store.dispatch({setter}({{ {prop_name}: {literal} }}));",
            }
    return {
        "page": page,
        "page_size": page_size,
        "ordering": _js(ordering),
        "sizes": sizes,
        "overrides": overrides,
        "setters": setters,
        "resets": resets,
    }


def _integer_literal(value: str, label: str) -> str:
    if not value.isdigit():
        raise GeneratorError("UNSUPPORTED_LIST", label)
    return value


def _attach_search(
    areas: list[dict[str, Any]],
    model: dict[str, Any],
    apis: list[dict[str, Any]],
    prefix: str,
    slug: str,
    header: str,
    mapper: TypeMapper,
    rules: dict[str, Any] | None,
    url: str,
) -> None:
    state_name = f"{prefix}State"
    for area in areas:
        area["fields"] = []
        area["buttons"] = []
        area["options"] = []
        area["form_class"] = ""
        area["form_import"] = ""
        area["form_path"] = ""
        area["form_module_import"] = ""
        area["form_context"] = None
        area["type_imports"] = []
        area["selector_imports"] = []
        area["action_imports"] = []
        area["state_name"] = state_name
        area["state_selector"] = f"select{prefix}State"
        area["needs_form"] = False
        area["needs_store"] = False
        area["needs_router"] = False
        area["needs_route"] = False
        area["paging"] = None
    routes = _route_binding(model, url, mapper)
    fields, form_area = _screen_fields(areas, model, mapper)
    if not fields:
        _assign_buttons(areas, _navigate_buttons(model, routes), [], None)
        _attach_paging(areas, model, apis, rules, None)
        return
    owners = [area for area in areas if area["area_type"] == form_area]
    if len(owners) != 1:
        raise GeneratorError("UNSUPPORTED_AREA", form_area)
    owner = owners[0]
    form_class = f"{prefix}QueryForm" if form_area == "QUERY" else f"{prefix}Form"
    form_path = f"{slug}/{owner['folder']}/{owner['file_stem']}.form.ts"
    option_params = _option_params(fields)
    owner["fields"] = fields
    owner["options"] = option_params
    owner["form_class"] = form_class
    owner["form_import"] = f"./{owner['file_stem']}.form"
    owner["form_path"] = form_path
    owner["form_module_import"] = f"./{owner['folder']}/{owner['file_stem']}.form"
    owner["type_imports"] = [param["element"] for param in option_params]
    owner["selector_imports"] = [param["selector"] for param in option_params]
    owner["table"] = _query_html(str(owner["area_type"]), fields)
    owner["form_context"] = {
        "header": header,
        "class_name": form_class,
        "slug": slug,
        "fields": [{"name": field["name"], "initial": '""'} for field in fields],
        "option_signature": ", ".join(
            f"{param['param']}: readonly {param['element']}[]" for param in option_params
        ),
        "type_imports": owner["type_imports"],
        "check_lines": [line for field in fields for line in field["checks"]],
        "valid_lines": [line for field in fields for line in _valid_lines(field)],
    }
    buttons = _search_buttons(
        model,
        apis,
        fields,
        option_params,
        rules,
        form_area,
        routes,
        _save_guard(model),
    )
    buttons.extend(_navigate_buttons(model, routes))
    _assign_buttons(areas, buttons, option_params, owner)
    _attach_paging(areas, model, apis, rules, owner)


def _screen_fields(
    areas: list[dict[str, Any]],
    model: dict[str, Any],
    mapper: TypeMapper,
) -> tuple[list[dict[str, Any]], str]:
    query = _query_fields(areas, model, mapper, "QUERY")
    form = _query_fields(areas, model, mapper, "FORM")
    if query and form:
        raise GeneratorError("UNSUPPORTED_AREA", "QUERY")
    if query:
        return query, "QUERY"
    if form:
        return form, "FORM"
    return [], ""


def _query_fields(
    areas: list[dict[str, Any]],
    model: dict[str, Any],
    mapper: TypeMapper,
    kind: str,
) -> list[dict[str, Any]]:
    area_type = {str(area["area_id"]): str(area["area_type"]) for area in areas}
    fields: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in model["inputs"]:
        if area_type.get(str(row["area_id"])) != kind:
            continue
        field = _query_field(row, model, mapper)
        if field["name"] in seen:
            raise GeneratorError("UNSUPPORTED_NAME", field["name"])
        seen.add(field["name"])
        fields.append(field)
    return fields


def _query_field(
    row: dict[str, Any],
    model: dict[str, Any],
    mapper: TypeMapper,
) -> dict[str, Any]:
    name = str(row["field_id"])
    label = str(row["label"])
    if not IDENT.fullmatch(name) or "\n" in label or "<" in label or "{{" in label:
        raise GeneratorError("UNSUPPORTED_INPUT", name)
    if str(row["data_type"]) != "string" or str(row["default_value"]) != "EMPTY":
        raise GeneratorError("UNSUPPORTED_INPUT", name)
    if str(row["validation_timing"]) != "ON_EXECUTE":
        raise GeneratorError("UNSUPPORTED_INPUT", name)
    ui = str(row["ui_type"])
    required, max_length, option_id = _parse_constraints(
        str(row["constraints"]),
        str(row["required"]),
    )
    if ui == "TEXT" and option_id:
        raise GeneratorError("UNSUPPORTED_INPUT", name)
    if ui == "SELECT" and not option_id:
        raise GeneratorError("UNSUPPORTED_INPUT", name)
    if ui not in {"TEXT", "SELECT"}:
        raise GeneratorError("UNSUPPORTED_INPUT", name)
    option = _option_binding(option_id, model, mapper) if option_id else None
    field: dict[str, Any] = {
        "name": name,
        "label": label,
        "ui": ui,
        "error": str(row["error_message"]),
        "required": required,
        "max_length": max_length,
        "option_param": "" if option is None else option["param"],
        "value_member": "" if option is None else option["value_member"],
        "display_member": "" if option is None else option["display_member"],
        "known": f"{name}IsKnown",
        "option": option,
    }
    field["checks"] = _check_lines(field)
    return field


def _parse_constraints(text: str, required_column: str) -> tuple[bool, int | None, str]:
    required = required_column == "Yes"
    max_length: int | None = None
    option_id = ""
    for token in text.split(";"):
        item = token.strip()
        if not item:
            continue
        if item == "required":
            required = True
            continue
        max_match = _MAX_LENGTH.fullmatch(item)
        if max_match:
            max_length = int(max_match.group(1))
            continue
        option_match = _OPTIONS.fullmatch(item)
        if option_match:
            option_id = option_match.group(1)
            continue
        raise GeneratorError("UNSUPPORTED_CONSTRAINT", item)
    return required, max_length, option_id


def _option_binding(
    option_id: str,
    model: dict[str, Any],
    mapper: TypeMapper,
) -> dict[str, str]:
    row = next((item for item in model["options"] if str(item["option_id"]) == option_id), None)
    if row is None or str(row["fetch_method"]) != "API":
        raise GeneratorError("UNSUPPORTED_OPTIONS", option_id)
    source = str(row["option_source"])
    if source.count(".") != 1:
        raise GeneratorError("UNSUPPORTED_OPTIONS", option_id)
    api_id, response_field = source.split(".", 1)
    destination = ""
    for mapping in model["response_mappings"]:
        if str(mapping["api_id"]) == api_id and str(mapping["response_field"]) == response_field:
            destination = str(mapping["destination"])
    state_paths = {str(item["state_path"]) for item in model["state_types"]}
    if destination not in state_paths:
        raise GeneratorError("UNSUPPORTED_OPTIONS", option_id)
    data_type = ""
    for item in model["state_types"]:
        if str(item["state_path"]) == destination:
            data_type = str(item["data_type"])
            if item["nullable"] == "Yes":
                raise GeneratorError("UNSUPPORTED_OPTIONS", option_id)
    base, is_array = split_type(data_type)
    if not is_array or base not in mapper.names:
        raise GeneratorError("UNSUPPORTED_OPTIONS", option_id)
    names = {
        str(item["field"])
        for item in model["named_type_fields"]
        if str(item["type_name"]) == base
    }
    display = str(row["display_value"])
    internal = str(row["internal_value"])
    if display not in names or internal not in names:
        raise GeneratorError("UNSUPPORTED_OPTIONS", option_id)
    return {
        "param": "options" + pascal(option_id),
        "selector": "select" + "".join(pascal(part) for part in destination.split(".")),
        "element": pascal(base),
        "value_member": member(internal),
        "display_member": member(display),
    }


def _option_params(fields: list[dict[str, Any]]) -> list[dict[str, str]]:
    params: list[dict[str, str]] = []
    seen: set[str] = set()
    for field in fields:
        option = field["option"]
        if option is None or option["param"] in seen:
            continue
        seen.add(option["param"])
        params.append(option)
    return params


def _field_access(field: dict[str, Any]) -> str:
    return f"value{member(str(field['name']))}"


def _field_probe(field: dict[str, Any]) -> str:
    access = _field_access(field)
    return (
        f"const {field['known']} = {field['option_param']}.some("
        f"(option) => option{field['value_member']} === {access});"
    )


def _field_arms(field: dict[str, Any]) -> list[str]:
    access = _field_access(field)
    arms: list[str] = []
    if field["required"]:
        arms.append(f'{access} === ""')
    if field["max_length"] is not None:
        arms.append(f"{access}.length > {field['max_length']}")
    if field["option_param"]:
        arms.append(f'{access} !== "" && !{field["known"]}')
    return arms


def _check_lines(field: dict[str, Any]) -> list[str]:
    key = _js(str(field["name"]))
    message = _js(str(field["error"]))
    lines: list[str] = []
    if field["option_param"]:
        lines.append(_field_probe(field))
    arms = _field_arms(field)
    for index, arm in enumerate(arms):
        prefix = "if" if index == 0 else "} else if"
        lines.append(f"{prefix} ({arm}) {{")
        lines.append(f"  messages[{key}] = {message};")
    if arms:
        lines.append("}")
    return lines


def _valid_lines(field: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if field["option_param"]:
        lines.append(_field_probe(field))
    for arm in _field_arms(field):
        lines.append(f"if ({arm}) {{")
        lines.append("  return false;")
        lines.append("}")
    return lines


def _save_guard(model: dict[str, Any]) -> dict[str, str] | None:
    rows = model["screen_specific"]["11.2"]
    if not rows:
        return None
    values = {str(row["item"]): str(row["value"]) for row in rows}
    required = (
        "保存API",
        "保存イベント",
        "保存前確認",
        "保存成功時遷移",
        "保存後フォーム初期化",
        "二重送信防止",
    )
    if any(item not in values for item in required):
        raise GeneratorError("UNSUPPORTED_ACTION", "11.2")
    if values["保存前確認"] != "No" or values["保存後フォーム初期化"] != "No":
        raise GeneratorError("UNSUPPORTED_ACTION", "11.2")
    if values["二重送信防止"] not in {"Yes", "No"}:
        raise GeneratorError("UNSUPPORTED_ACTION", "二重送信防止")
    if values["二重送信防止"] == "No":
        return None
    return {
        "api_id": values["保存API"],
        "event_id": values["保存イベント"],
    }


def _search_buttons(
    model: dict[str, Any],
    apis: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    option_params: list[dict[str, str]],
    rules: dict[str, Any] | None,
    form_area: str,
    routes: dict[str, dict[str, str]],
    guard: dict[str, str] | None,
) -> list[dict[str, Any]]:
    by_id = {str(api["api_id"]): api for api in apis}
    nav_by_id = {str(row["nav_id"]): row for row in model["navigation"]}
    paths = {str(row["state_path"]) for row in model["state_types"]}
    controls = {str(field["name"]) for field in fields}
    steps_by_event: dict[str, list[dict[str, Any]]] = {}
    for step in model["event_steps"]:
        steps_by_event.setdefault(str(step["event_id"]), []).append(step)
    buttons: list[dict[str, Any]] = []
    for action in model["actions"]:
        if str(action["ui_type"]) != "BUTTON":
            continue
        event_id = str(action["event_id"])
        steps = sorted(
            steps_by_event.get(event_id, []),
            key=lambda row: int(row["step"]),
        )
        built = _search_calls(
            steps,
            by_id,
            paths,
            controls,
            rules,
            form_area,
            event_id,
            nav_by_id,
            routes,
        )
        if built is None:
            continue
        if str(action["visibility_condition"]) != "ALWAYS":
            raise GeneratorError("UNSUPPORTED_ACTION", str(action["field_id"]))
        method = str(action["field_id"])
        label = str(action["label"])
        if not IDENT.fullmatch(method) or "\n" in label or "<" in label:
            raise GeneratorError("UNSUPPORTED_ACTION", method)
        disabled = _disabled_expression(str(action["enabled_condition"]), option_params, method)
        submit_guard = _submit_guard(guard, event_id, method, built)
        loading_guard = _loading_guard(
            str(action["enabled_condition"]),
            method,
            built,
            submit_guard is not None,
        )
        for watched in (submit_guard, loading_guard):
            if watched is None:
                continue
            signal_name = str(watched["signal"])
            disabled = (
                f"{disabled} || this.{signal_name}()" if disabled else f"this.{signal_name}()"
            )
        buttons.append(
            {
                "area_id": str(action["area_id"]),
                "method": method,
                "label": label,
                "actions": _unique(
                    [str(call["action"]) for call in built]
                    + [name for call in built for name in call["setter_names"]]
                    + (
                        []
                        if submit_guard is None
                        else [str(submit_guard["success"]), str(submit_guard["failure"])]
                    )
                    + (
                        []
                        if loading_guard is None
                        else [
                            str(loading_guard["action"]),
                            str(loading_guard["success"]),
                            str(loading_guard["failure"]),
                        ]
                    )
                ),
                "request_names": [
                    str(call["request_name"]) for call in built if call["request_name"]
                ],
                "needs_form": True,
                "needs_store": True,
                "needs_state": any(
                    bool(call["state_fields"] or call["setter_lines"]) for call in built
                ),
                "needs_router": False,
                "needs_route": any(bool(call["route_fields"]) for call in built),
                "disabled_method": f"{method}Disabled" if disabled else "",
                "disabled_lines": [f"return {disabled};"] if disabled else [],
                "navigate": built[-1].get("navigate"),
                "submit_guard": submit_guard,
                "loading_guard": loading_guard,
                "lines": _button_lines(
                    built,
                    option_params,
                    "" if submit_guard is None else str(submit_guard["signal"]),
                    "" if loading_guard is None else str(loading_guard["signal"]),
                ),
            }
        )
    if guard is not None and not any(button["submit_guard"] for button in buttons):
        raise GeneratorError("UNSUPPORTED_ACTION", "二重送信防止")
    return buttons


def _loading_guard(
    condition: str,
    method: str,
    calls: list[dict[str, Any]],
    has_submit_guard: bool,
) -> dict[str, str] | None:
    parts = [part.strip() for part in condition.split("&&")]
    if "NOT_LOADING" not in parts:
        return None
    if has_submit_guard:
        return None
    if len(calls) != 1:
        raise GeneratorError("UNSUPPORTED_ACTION", method)
    call = calls[0]
    return {
        "signal": f"{method}Loading",
        "action": str(call["action"]),
        "success": str(call["success"]),
        "failure": str(call["failure"]),
    }


def _submit_guard(
    guard: dict[str, str] | None,
    event_id: str,
    method: str,
    calls: list[dict[str, Any]],
) -> dict[str, str] | None:
    if guard is None or event_id != guard["event_id"]:
        return None
    matched = [call for call in calls if str(call["api_id"]) == guard["api_id"]]
    if len(calls) != 1 or len(matched) != 1:
        raise GeneratorError("UNSUPPORTED_ACTION", "二重送信防止")
    call = matched[0]
    return {
        "signal": f"{method}Submitting",
        "success": str(call["success"]),
        "failure": str(call["failure"]),
    }


def _disabled_expression(
    condition: str,
    option_params: list[dict[str, str]],
    method: str,
) -> str:
    if condition in {"ALWAYS", "NOT_LOADING"}:
        return ""
    parts = [part.strip() for part in condition.split("&&")]
    if not parts or any(part not in {"FORM_VALID", "NOT_LOADING"} for part in parts):
        raise GeneratorError("UNSUPPORTED_ACTION", method)
    if "FORM_VALID" not in parts:
        return ""
    args = ", ".join(f"this.{param['param']}()" for param in option_params)
    return f"!this.queryForm.isValid({args})"


def _navigate_buttons(
    model: dict[str, Any],
    routes: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    steps_by_event: dict[str, list[dict[str, Any]]] = {}
    for step in model["event_steps"]:
        steps_by_event.setdefault(str(step["event_id"]), []).append(step)
    nav_by_id = {str(row["nav_id"]): row for row in model["navigation"]}
    buttons: list[dict[str, Any]] = []
    for action in model["actions"]:
        if str(action["ui_type"]) != "BUTTON":
            continue
        steps = sorted(
            steps_by_event.get(str(action["event_id"]), []),
            key=lambda row: int(row["step"]),
        )
        plan = _navigate_plan(steps, str(action["event_id"]), nav_by_id, routes)
        if plan is None:
            continue
        if str(action["visibility_condition"]) != "ALWAYS":
            raise GeneratorError("UNSUPPORTED_ACTION", str(action["field_id"]))
        if str(action["enabled_condition"]) not in {"ALWAYS", "NOT_LOADING"}:
            raise GeneratorError("UNSUPPORTED_ACTION", str(action["field_id"]))
        method = str(action["field_id"])
        label = str(action["label"])
        if not IDENT.fullmatch(method) or "\n" in label or "<" in label:
            raise GeneratorError("UNSUPPORTED_ACTION", method)
        buttons.append(
            {
                "area_id": str(action["area_id"]),
                "method": method,
                "label": label,
                "actions": [],
                "request_names": [],
                "needs_form": False,
                "needs_store": False,
                "needs_state": False,
                "needs_router": True,
                "needs_route": bool(plan["reads"]),
                "disabled_method": "",
                "disabled_lines": [],
                "submit_guard": None,
                "loading_guard": None,
                "navigate": None,
                "lines": plan["lines"],
            }
        )
    return buttons


def _navigate_plan(
    steps: list[dict[str, Any]],
    event_id: str,
    nav_by_id: dict[str, dict[str, Any]],
    routes: dict[str, dict[str, str]],
) -> dict[str, Any] | None:
    if not steps or any(str(step["condition"]) != "ALWAYS" for step in steps):
        return None
    if any(str(step["operation"]) != "NAVIGATE" for step in steps):
        return None
    plans: list[dict[str, Any]] = []
    for step in steps:
        nav = nav_by_id.get(str(step["reference"]))
        plan = None if nav is None else _nav_plan(nav, event_id, routes)
        if plan is None:
            return None
        plans.append(plan)
    if len(plans) != 1:
        return None
    return plans[0]


def _nav_plan(
    nav: dict[str, Any],
    event_id: str,
    routes: dict[str, dict[str, str]],
) -> dict[str, Any] | None:
    if str(nav["event_id"]) != event_id or str(nav["condition"]) != "ALWAYS":
        return None
    parameters = str(nav["parameters"]).strip()
    target = str(nav["target"])
    if parameters == "NONE":
        literal = _none_parameter_target(nav, event_id)
        if literal is None:
            return None
        return {
            "reads": [],
            "lines": [f"this.router.navigateByUrl({_js(literal)});"],
        }
    reads: list[dict[str, str]] = []
    marked = target
    for part in parameters.split(","):
        match = _ROUTE_ASSIGN.fullmatch(part.strip())
        if match is None or match.group(1) != match.group(2):
            return None
        name = match.group(1)
        route = routes.get(f"route.{name}")
        if route is None:
            return None
        token = "{" + name + "}"
        if marked.count(token) != 1:
            raise GeneratorError("UNSUPPORTED_NAVIGATION", str(nav["nav_id"]))
        marked = marked.replace(token, "\0" + name + "\0", 1)
        reads.append(route)
    if "{" in marked or "}" in marked or any(char.isspace() for char in target):
        raise GeneratorError("UNSUPPORTED_NAVIGATION", str(nav["nav_id"]))
    pieces = marked.split("\0")
    parts: list[str] = []
    for index, piece in enumerate(pieces):
        if index % 2 == 0:
            if piece:
                parts.append(_js(piece))
            continue
        parts.append(f"encodeURIComponent({piece})")
    lines: list[str] = []
    for route in reads:
        name = str(route["name"])
        lines.extend(
            [
                f"const {name} = this.route.snapshot.paramMap.get({route['literal']});",
                f"if ({name} === null || !/^(0|[1-9]\\d*)$/.test({name})) {{",
                "  return;",
                "}",
            ]
        )
    lines.append(f"this.router.navigateByUrl({' + '.join(parts)});")
    return {"reads": reads, "lines": lines}


def _none_parameter_target(nav: dict[str, Any], event_id: str) -> str | None:
    if str(nav["event_id"]) != event_id or str(nav["condition"]) != "ALWAYS":
        return None
    if str(nav["parameters"]) != "NONE":
        return None
    target = str(nav["target"])
    if (
        not target.startswith("/")
        or "{" in target
        or "}" in target
        or ":" in target
        or any(char.isspace() for char in target)
    ):
        raise GeneratorError("UNSUPPORTED_NAVIGATION", str(nav["nav_id"]))
    return target


def _assign_buttons(
    areas: list[dict[str, Any]],
    buttons: list[dict[str, Any]],
    option_params: list[dict[str, str]],
    owner: dict[str, Any] | None,
) -> None:
    for area in areas:
        owned = [button for button in buttons if button["area_id"] == area["area_id"]]
        if not owned:
            continue
        area["buttons"] = owned
        area["needs_form"] = any(button["needs_form"] for button in owned)
        area["needs_store"] = any(button["needs_store"] for button in owned)
        area["needs_state"] = any(button["needs_state"] for button in owned)
        area["needs_router"] = any(button["needs_router"] for button in owned)
        area["needs_route"] = any(button["needs_route"] for button in owned)
        area["needs_submit_guard"] = any(button["submit_guard"] for button in owned)
        area["needs_loading_guard"] = any(button["loading_guard"] for button in owned)
        area["options"] = option_params if area["needs_store"] else []
        if area["needs_form"]:
            if owner is None:
                raise GeneratorError("UNSUPPORTED_ACTION", str(area["area_id"]))
            area["form_class"] = str(owner["form_class"])
            area["form_path"] = str(owner["form_path"])
            if area["folder"] == owner["folder"]:
                area["form_import"] = f"./{owner['file_stem']}.form"
            else:
                area["form_import"] = f"../{owner['folder']}/{owner['file_stem']}.form"
        if area["needs_store"]:
            area["type_imports"] = _unique(
                [name for button in owned for name in button["request_names"]]
                + [param["element"] for param in option_params]
            )
            selectors = [param["selector"] for param in option_params]
            if area["needs_state"]:
                selectors.insert(0, str(area["state_selector"]))
            area["selector_imports"] = _unique(selectors)
            area["action_imports"] = _unique(
                [name for button in owned for name in button["actions"]]
            )
        area["table"] = _actions_html(str(area["area_type"]), owned)


def _attach_paging(
    areas: list[dict[str, Any]],
    model: dict[str, Any],
    apis: list[dict[str, Any]],
    rules: dict[str, Any] | None,
    owner: dict[str, Any] | None,
) -> None:
    if rules is None or owner is None:
        return
    lists = [area for area in areas if area["area_type"] == "LIST" and area["columns"]]
    if len(lists) != 1:
        raise GeneratorError("UNSUPPORTED_LIST", "LIST")
    area = lists[0]
    controls = _paging_controls(model, apis, owner, rules)
    if not controls:
        return
    area["paging"] = {
        "request_name": controls[0]["request_name"],
        "selectors": _unique(
            [str(area["state_selector"])] + [str(control["selector"]) for control in controls]
        ),
        "action_imports": _unique(
            [str(control["action"]) for control in controls]
            + [str(setter["name"]) for setter in rules["setters"]]
        ),
        "sizes": ", ".join(str(size) for size in rules["sizes"]),
        "signals": [
            {"name": str(control["signal"]), "selector": str(control["selector"])}
            for control in controls
        ],
        "methods": controls,
    }
    area["form_class"] = str(owner["form_class"])
    area["form_path"] = str(owner["form_path"])
    area["form_import"] = f"../{owner['folder']}/{owner['file_stem']}.form"
    area["state_name"] = str(area["state_name"])
    html = _paging_html(controls)
    table = str(area["table"])
    closing = "</section>"
    if not table.endswith(closing):
        raise GeneratorError("UNSUPPORTED_LIST", "LIST")
    area["table"] = table[: -len(closing)] + html + closing


def _paging_controls(
    model: dict[str, Any],
    apis: list[dict[str, Any]],
    owner: dict[str, Any],
    rules: dict[str, Any],
) -> list[dict[str, Any]]:
    by_id = {str(api["api_id"]): api for api in apis}
    paths = {str(row["state_path"]) for row in model["state_types"]}
    controls_by_id = {str(field["name"]) for field in owner["fields"]}
    steps_by_event: dict[str, list[dict[str, Any]]] = {}
    for step in model["event_steps"]:
        steps_by_event.setdefault(str(step["event_id"]), []).append(step)
    controls: list[dict[str, Any]] = []
    for event in model["events"]:
        triggers = {item.strip() for item in str(event["trigger"]).split(",")}
        if "ON_CHANGE" not in triggers:
            continue
        origin = str(event["origin"])
        if origin not in {"pagination.page", "pagination.pageSize", "sort.ordering"}:
            continue
        steps = sorted(
            steps_by_event.get(str(event["event_id"]), []),
            key=lambda row: int(row["step"]),
        )
        if not steps or any(str(step["condition"]) != "ALWAYS" for step in steps):
            continue
        if any(str(step["operation"]) not in {"RESET_PAGE", "CALL_API"} for step in steps):
            continue
        if not any(str(step["operation"]) == "CALL_API" for step in steps):
            continue
        if any(
            str(step["operation"]) == "RESET_PAGE" and str(step["reference"]) != "pagination.page"
            for step in steps
        ):
            continue
        call = None
        for step in steps:
            if str(step["operation"]) != "CALL_API":
                continue
            call = _form_call(
                by_id.get(str(step["reference"])),
                paths,
                controls_by_id,
                apply_query=False,
                use_applied=True,
                resets={},
            )
            if call is None:
                call = None
                break
        if call is None:
            continue
        built = _paging_method(origin, str(event["event_name"]), call, rules)
        if built is None:
            continue
        controls.append(built)
    return controls


def _paging_method(
    origin: str,
    label: str,
    call: dict[str, Any],
    rules: dict[str, Any],
) -> dict[str, Any] | None:
    signal = origin.split(".")[-1]
    if not IDENT.fullmatch(signal) or "\n" in label or "<" in label:
        raise GeneratorError("UNSUPPORTED_LIST", origin)
    method = "change" + "".join(pascal(part) for part in origin.split("."))
    selector = "select" + "".join(pascal(part) for part in origin.split("."))
    lines = ["const element = event.target;"]
    replacements: dict[str, str] = {}
    setters: list[str] = []
    kind = "text"
    if origin == "pagination.page":
        kind = "number"
        lines.extend(
            [
                "if (!(element instanceof HTMLInputElement)) {",
                "  return;",
                "}",
                "const page = Number(element.value);",
                "if (!Number.isInteger(page)) {",
                "  return;",
                "}",
            ]
        )
        replacements = {"page": "page"}
        setters = ["this.store.dispatch(setPaginationPage({ page }));"]
    elif origin == "pagination.pageSize":
        kind = "select"
        lines.extend(
            [
                "if (!(element instanceof HTMLSelectElement)) {",
                "  return;",
                "}",
                "const pageSize = Number(element.value);",
                "if (!this.pageSizes.includes(pageSize)) {",
                "  return;",
                "}",
                f"const page = {rules['page']};",
            ]
        )
        replacements = {"page": "page", "page_size": "pageSize"}
        setters = [
            "this.store.dispatch(setPaginationPageSize({ pageSize }));",
            "this.store.dispatch(setPaginationPage({ page }));",
        ]
    elif origin == "sort.ordering":
        lines.extend(
            [
                "if (!(element instanceof HTMLInputElement)) {",
                "  return;",
                "}",
                "const ordering = element.value;",
                f"const page = {rules['page']};",
            ]
        )
        replacements = {"page": "page", "ordering": "ordering"}
        setters = [
            "this.store.dispatch(setSortOrdering({ ordering }));",
            "this.store.dispatch(setPaginationPage({ page }));",
        ]
    else:
        return None
    lines.extend(
        [
            "const value = this.queryForm.applied();",
            "const state = this.state();",
            *setters,
        ]
    )
    fields = [(name, replacements.get(name, expr)) for name, expr in call["state_fields"]]
    rewritten = {**call, "state_fields": fields}
    lines.extend(_request_lines("request", rewritten))
    lines.append(f"this.store.dispatch({call['action']}(request));")
    return {
        "method": method,
        "label": label,
        "signal": signal,
        "selector": selector,
        "kind": kind,
        "lines": lines,
        "request_name": str(call["request_name"]),
        "action": str(call["action"]),
        "control_id": origin.replace(".", "-"),
    }


def _paging_html(controls: list[dict[str, Any]]) -> str:
    lines = ["  <div>"]
    for control in controls:
        label = _html(str(control["label"]))
        control_id = str(control["control_id"])
        signal = str(control["signal"])
        method = str(control["method"])
        lines.append(f'    <label for="{control_id}">{label}</label>')
        if control["kind"] == "select":
            lines.append(
                f'    <select id="{control_id}" [value]="{signal}().toString()" '
                f'(change)="{method}($event)">'
            )
            lines.append("      @for (size of pageSizes; track size) {")
            lines.append('        <option [value]="size">{{ size }}</option>')
            lines.append("      }")
            lines.append("    </select>")
        elif control["kind"] == "number":
            lines.append(
                f'    <input id="{control_id}" type="number" [value]="{signal}()" '
                f'(change)="{method}($event)" />'
            )
        else:
            lines.append(
                f'    <input id="{control_id}" type="text" [value]="{signal}()" '
                f'(change)="{method}($event)" />'
            )
    lines.append("  </div>")
    return "\n".join(lines) + "\n"


def _search_calls(
    steps: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
    paths: set[str],
    controls: set[str],
    rules: dict[str, Any] | None,
    form_area: str,
    event_id: str,
    nav_by_id: dict[str, dict[str, Any]],
    routes: dict[str, dict[str, str]],
) -> list[dict[str, Any]] | None:
    if not steps or any(str(step["condition"]) != "ALWAYS" for step in steps):
        return None
    if any(str(step["operation"]) not in _SEARCH_OPS for step in steps):
        return None
    if not any(str(step["operation"]) == "CALL_API" for step in steps):
        return None
    nav_steps = [step for step in steps if str(step["operation"]) == "NAVIGATE"]
    if nav_steps and (len(nav_steps) != 1 or steps[-1] is not nav_steps[0]):
        return None
    apply_query = any(str(step["operation"]) == "APPLY_QUERY" for step in steps)
    resets = {} if rules is None else rules["resets"]
    for step in steps:
        operation = str(step["operation"])
        reference = str(step["reference"])
        if operation == "VALIDATE" and reference != form_area:
            return None
        if operation == "APPLY_QUERY" and reference != "QUERY":
            return None
        if operation == "RESET_PAGE" and reference not in resets:
            return None
    active = {
        str(step["reference"]): resets[str(step["reference"])]
        for step in steps
        if str(step["operation"]) == "RESET_PAGE"
    }
    calls: list[dict[str, Any]] = []
    for step in steps:
        if str(step["operation"]) != "CALL_API":
            continue
        call = _form_call(
            by_id.get(str(step["reference"])),
            paths,
            controls,
            apply_query=apply_query,
            use_applied=True,
            resets=active,
            routes=routes,
        )
        if call is None:
            return None
        calls.append(call)
    if nav_steps:
        if len(calls) != 1:
            return None
        target = _step_target(nav_steps[0], event_id, nav_by_id)
        if target is None:
            return None
        calls[-1]["navigate"] = {"success": str(calls[-1]["success"]), "target": target}
    return calls


def _step_target(
    step: dict[str, Any],
    event_id: str,
    nav_by_id: dict[str, dict[str, Any]],
) -> str | None:
    nav = nav_by_id.get(str(step["reference"]))
    if nav is None:
        return None
    return _none_parameter_target(nav, event_id)


def _form_call(
    api: dict[str, Any] | None,
    paths: set[str],
    controls: set[str],
    *,
    apply_query: bool,
    use_applied: bool,
    resets: dict[str, dict[str, str]],
    routes: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any] | None:
    if api is None:
        return None
    route_bindings = {} if routes is None else routes
    state_fields: list[tuple[str, str]] = []
    form_fields: list[tuple[str, str, bool, str]] = []
    route_fields: list[tuple[str, str]] = []
    route_reads: list[dict[str, str]] = []
    setter_names: list[str] = []
    setter_lines: list[str] = []
    for param in api["params"]:
        source = str(param["source"])
        expr = _state_expr(source, paths)
        if expr is not None:
            reset = resets.get(source)
            if reset is None:
                state_fields.append((str(param["name"]), expr))
            else:
                state_fields.append((str(param["name"]), reset["literal"]))
                if reset["name"] not in setter_names:
                    setter_names.append(reset["name"])
                    setter_lines.append(reset["dispatch"])
            continue
        if (apply_query or use_applied) and source.startswith("query.applied."):
            control = source.removeprefix("query.applied.")
            if control in controls:
                form_fields.append((str(param["name"]), control, bool(param["optional"]), "value"))
                continue
        if source.startswith("input."):
            control = source.removeprefix("input.")
            if control in controls:
                form_fields.append((str(param["name"]), control, bool(param["optional"]), "input"))
                continue
        route = route_bindings.get(source)
        if route is not None:
            route_fields.append((str(param["name"]), str(route["name"])))
            if not any(item["name"] == route["name"] for item in route_reads):
                route_reads.append(route)
            continue
        if param["optional"]:
            continue
        return None
    return {
        "api_id": str(api["api_id"]),
        "action": str(api["action"]),
        "success": str(api["success"]),
        "failure": str(api["failure"]),
        "request_name": str(api["request_name"]),
        "state_fields": state_fields,
        "form_fields": form_fields,
        "route_fields": route_fields,
        "route_reads": route_reads,
        "apply_query": apply_query,
        "setter_names": setter_names,
        "setter_lines": setter_lines,
    }


def _button_lines(
    calls: list[dict[str, Any]],
    option_params: list[dict[str, str]],
    submitting: str = "",
    loading: str = "",
) -> list[str]:
    args = ", ".join(f"this.{param['param']}()" for param in option_params)
    lines = []
    if loading:
        lines.extend(
            [
                f"if (this.{loading}()) {{",
                "  return;",
                "}",
            ]
        )
    if submitting:
        lines.extend(
            [
                f"if (this.{submitting}()) {{",
                "  return;",
                "}",
            ]
        )
    lines.extend(
        [
            f"if (!this.queryForm.validate({args})) {{",
            "  return;",
            "}",
        ]
    )
    if any(call["apply_query"] for call in calls):
        lines.append("this.queryForm.applyQuery();")
    seen_routes: set[str] = set()
    for call in calls:
        for route in call["route_reads"]:
            name = str(route["name"])
            if name in seen_routes:
                continue
            seen_routes.add(name)
            lines.extend(
                [
                    f"const {name} = this.route.snapshot.paramMap.get({route['literal']});",
                    f"if ({name} === null || !/^(0|[1-9]\\d*)$/.test({name})) {{",
                    "  return;",
                    "}",
                ]
            )
    reads_value = any(source == "value" for call in calls for *_, source in call["form_fields"])
    reads_input = any(source == "input" for call in calls for *_, source in call["form_fields"])
    reads_state = any(call["state_fields"] or call["setter_lines"] for call in calls)
    if reads_value:
        lines.append("const value = this.queryForm.applied();")
    if reads_input:
        lines.append("const input = this.queryForm.form.getRawValue();")
    if reads_state:
        lines.append("const state = this.state();")
    for index, call in enumerate(calls):
        lines.extend(call["setter_lines"])
        if not call["request_name"]:
            if submitting:
                lines.append(f"this.{submitting}.set(true);")
            lines.append(f"this.store.dispatch({call['action']}());")
            continue
        variable = "request" if index == 0 else f"request{index + 1}"
        lines.extend(_request_lines(variable, call))
        if submitting:
            lines.append(f"this.{submitting}.set(true);")
        lines.append(f"this.store.dispatch({call['action']}({variable}));")
    return lines


def _request_lines(variable: str, call: dict[str, Any]) -> list[str]:
    if not call["request_name"]:
        return []
    lines = [f"const {variable}: {call['request_name']} = {{"]
    for name, expr in call["state_fields"]:
        lines.append(f"  {prop(name)}: {expr},")
    for name, route_name in call["route_fields"]:
        lines.append(f"  {prop(name)}: Number({route_name}),")
    deferred: list[tuple[str, str, str]] = []
    for name, control, optional, source in call["form_fields"]:
        if optional:
            deferred.append((name, control, source))
            continue
        lines.append(f"  {prop(name)}: {source}{member(control)},")
    lines.append("};")
    for name, control, source in deferred:
        lines.append(f'if ({source}{member(control)} !== "") {{')
        lines.append(f"  {variable}{member(name)} = {source}{member(control)};")
        lines.append("}")
    return lines


def _actions_html(area_type: str, buttons: list[dict[str, Any]]) -> str:
    lines = [f'<section data-area-type="{_html(area_type)}">']
    for button in buttons:
        label = _html(str(button["label"]))
        disabled = str(button.get("disabled_method", ""))
        if disabled:
            lines.append(
                f'  <button type="button" [disabled]="{disabled}()" '
                f'(click)="{button["method"]}()">{label}</button>'
            )
        else:
            lines.append(
                f'  <button type="button" (click)="{button["method"]}()">{label}</button>'
            )
    lines.append("</section>")
    return "\n".join(lines)


def _query_html(area_type: str, fields: list[dict[str, Any]]) -> str:
    lines = [
        f'<section data-area-type="{_html(area_type)}">',
        '  <form [formGroup]="queryForm.form">',
    ]
    for field in fields:
        name = str(field["name"])
        lines.extend(_control_html(field, name))
    lines.extend(["  </form>", "</section>"])
    return "\n".join(lines)


def _control_html(field: dict[str, Any], name: str) -> list[str]:
    label = _html(str(field["label"]))
    invalid = f"queryForm.messages().{name} ? true : null"
    described = f"queryForm.messages().{name} ? '{name}-error' : null"
    lines = [
        "    <div>",
        f'      <label for="{name}">{label}</label>',
    ]
    if field["ui"] == "TEXT":
        lines.append(
            f'      <input id="{name}" type="text" formControlName="{name}" '
            f'[attr.aria-invalid]="{invalid}" [attr.aria-describedby]="{described}" />'
        )
    else:
        lines.append(
            f'      <select id="{name}" formControlName="{name}" '
            f'[attr.aria-invalid]="{invalid}" [attr.aria-describedby]="{described}">'
        )
        lines.append('        <option value=""></option>')
        track = f"option{field['value_member']}"
        text = f"option{field['display_member']}"
        lines.append(f"        @for (option of {field['option_param']}(); track {track}) {{")
        lines.append(f'          <option [value]="{track}">{{{{ {text} }}}}</option>')
        lines.append("        }")
        lines.append("      </select>")
    lines.append(f"      @if (queryForm.messages().{name}) {{")
    lines.append(f'        <p id="{name}-error">{{{{ queryForm.messages().{name} }}}}</p>')
    lines.append("      }")
    lines.append("    </div>")
    return lines


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _state_type_name(model: dict[str, Any], mapper: TypeMapper, path: str) -> str:
    for row in model["state_types"]:
        if str(row["state_path"]) == path:
            return mapper.ts(str(row["data_type"]), nullable=row["nullable"] == "Yes")
    raise GeneratorError("UNSUPPORTED_STATE", path)


def _named_imports(model: dict[str, Any], mapper: TypeMapper, path: str) -> list[str]:
    for row in model["state_types"]:
        if str(row["state_path"]) != path:
            continue
        base, _is_array = split_type(str(row["data_type"]))
        if base in mapper.names:
            return [pascal(base)]
        return []
    return []


def _model_import(feature: str, slug: str, type_names: list[str], import_codes: bool) -> str:
    parts: list[str] = []
    if import_codes:
        parts.append(f"{feature}Codes")
    parts.extend(f"type {name}" for name in type_names)
    if not parts:
        return ""
    joined = ", ".join(parts)
    return f'import {{ {joined} }} from "../models/{slug}.models";'


def _code_groups(rows: list[dict[str, Any]], used: set[str]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        code_id = str(row["code_id"])
        if code_id not in used:
            continue
        grouped.setdefault(code_id, []).append(
            {
                "literal": _js(str(row["code"])),
                "member": member(str(row["code"])),
            }
        )
    return [
        {"literal": _js(code_id), "key": prop(code_id), "rows": items}
        for code_id, items in grouped.items()
    ]


def _row_nav(url: str, columns: list[dict[str, str]]) -> dict[str, str] | None:
    matched = [
        column for column in columns if column["field"] == "id" and column["data_type"] == "integer"
    ]
    if len(matched) != 1:
        return None
    if (
        not url.startswith("/")
        or url.endswith("/")
        or "{" in url
        or "}" in url
        or ":" in url
        or any(char.isspace() for char in url)
    ):
        return None
    return {"literal": _js(url)}


def _empty_result(
    model: dict[str, Any],
    apis: list[dict[str, Any]],
    collection: str,
) -> dict[str, str] | None:
    message: str | None = None
    for row in model["screen_errors"]:
        if str(row["condition"]) != "検索結果0件":
            continue
        if str(row["behavior"]) != "空状態を表示":
            raise GeneratorError("UNSUPPORTED_AREA", str(row["error_id"]))
        text = str(row["message"])
        if message is not None or not text or "\n" in text or "<" in text:
            raise GeneratorError("UNSUPPORTED_AREA", str(row["error_id"]))
        message = text
    if message is None:
        return None
    found = [
        str(api["success"])
        for api in apis
        if any(".".join(segments) == collection for segments, _expr in api["updates"])
    ]
    if len(found) != 1:
        raise GeneratorError("UNSUPPORTED_AREA", collection)
    return {"message": message, "success": found[0]}


def _render_table(
    area_type: str,
    columns: list[dict[str, str]],
    track: str,
    linked: bool,
    empty_message: str | None,
) -> str:
    lines = [
        f'<section data-area-type="{_html(area_type)}">',
        "  <table>",
        "    <thead>",
        "      <tr>",
    ]
    for column in columns:
        lines.append(f'        <th scope="col">{_html(column["label"])}</th>')
    if linked:
        lines.append('        <th scope="col">編集</th>')
    row = '        <tr (click)="openRow(item.id)" (keydown.enter)="openRow(item.id)" tabindex="0">'
    lines.extend(
        [
            "      </tr>",
            "    </thead>",
            "    <tbody>",
            f"      @for (item of items(); track {track}) {{",
            row if linked else "        <tr>",
        ]
    )
    for column in columns:
        access = f"item{column['member']}"
        empty = _js(column["empty"])
        if column["code_id"]:
            group = _js(column["code_id"])
            expr = f"{{{{ codeLabel({group}, {access}, {empty}) }}}}"
        else:
            expr = f'{{{{ {access} == null || {access} === "" ? {empty} : {access} }}}}'
        lines.append(f"          <td>{expr}</td>")
    if linked:
        lines.extend(
            [
                "          <td>",
                '            <button type="button" aria-label="編集" '
                '(click)="openRowEdit(item.id, $event)" '
                '(keydown.enter)="$event.stopPropagation()">',
                '              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
                'viewBox="0 0 16 16" aria-hidden="true" focusable="false">',
                '                <path d="M11.5 1.5l3 3L5 14H2v-3L11.5 1.5z" fill="none" '
                'stroke="currentColor" stroke-width="1.2"/>',
                "              </svg>",
                "            </button>",
                "          </td>",
            ]
        )
    lines.extend(
        [
            "        </tr>",
            "      }",
            "    </tbody>",
            "  </table>",
        ]
    )
    if empty_message:
        lines.extend(
            [
                "  @if (listReceived() && items().length === 0) {",
                f"    <p>{_html(empty_message)}</p>",
                "  }",
            ]
        )
    lines.append("</section>")
    return "\n".join(lines)


def _html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _init_plan(
    model: dict[str, Any],
    apis: list[dict[str, Any]],
    url: str,
    mapper: TypeMapper,
) -> dict[str, Any]:
    by_id = {str(api["api_id"]): api for api in apis}
    by_init = {str(step["init_id"]): step for step in model["initialization"]}
    paths = {str(row["state_path"]) for row in model["state_types"]}
    steps_by_event: dict[str, list[dict[str, Any]]] = {}
    for step in model["event_steps"]:
        steps_by_event.setdefault(str(step["event_id"]), []).append(step)
    calls: list[str] = []
    routes: list[dict[str, str]] = []
    seen_routes: set[str] = set()
    reads_state = False
    for step in model["initialization"]:
        operation = str(step["operation"])
        reference = str(step["reference"])
        targets: list[dict[str, Any] | None] = []
        if operation == "CALL_API":
            targets.append(by_id.get(reference))
        elif operation == "CALL_EVENT":
            event_steps = sorted(
                steps_by_event.get(reference, []),
                key=lambda row: int(row["step"]),
            )
            targets.extend(
                by_id.get(str(event_step["reference"]))
                for event_step in event_steps
                if str(event_step["operation"]) == "CALL_API"
            )
        allowed = _route_allowed(step, by_init, model)
        for api in targets:
            built = _dispatch_call(api, paths, _route_binding(model, url, mapper), allowed)
            if built is None:
                continue
            calls.append(built["snippet"])
            reads_state = reads_state or built["reads_state"]
            for route in built["routes"]:
                if route["name"] in seen_routes:
                    continue
                seen_routes.add(route["name"])
                routes.append(route)
    return {"calls": calls, "routes": routes, "reads_state": reads_state}


def _route_allowed(
    step: dict[str, Any],
    by_init: dict[str, dict[str, Any]],
    model: dict[str, Any],
) -> set[str]:
    raw = str(step["depends_on"]).strip()
    if raw == "NONE":
        return set()
    allowed: set[str] = set()
    for dep_id in raw.split(","):
        parent = by_init.get(dep_id.strip())
        if parent is None or str(parent["condition"]) != "ALWAYS":
            return set()
        operation = str(parent["operation"])
        if operation == "READ_ROUTE":
            allowed.add(str(parent["reference"]))
            continue
        if operation == "APPLY_DEFAULTS" and _empty_input_defaults(model):
            continue
        return set()
    return allowed


def _empty_input_defaults(model: dict[str, Any]) -> bool:
    inputs = {str(row["field_id"]) for row in model["inputs"]}
    defaults = model["defaults"]
    if not defaults:
        return False
    for row in defaults:
        destination = str(row["destination"])
        control = destination.removeprefix("input.")
        if (
            not destination.startswith("input.")
            or control not in inputs
            or str(row["value"]) != "EMPTY"
        ):
            return False
    return True


def _route_binding(
    model: dict[str, Any],
    url: str,
    mapper: TypeMapper,
) -> dict[str, dict[str, str]]:
    segments = url.split("/")
    bindings: dict[str, dict[str, str]] = {}
    for row in model["route_parameters"]:
        name = str(row["parameter"])
        destination = str(row["destination"])
        if str(row["kind"]) != "PATH" or str(row["required"]) != "Yes":
            raise GeneratorError("UNSUPPORTED_ROUTE", name)
        if destination != f"route.{name}" or f":{name}" not in segments:
            raise GeneratorError("UNSUPPORTED_ROUTE", destination)
        if str(row["data_type"]) != "integer" or not IDENT.fullmatch(name):
            raise GeneratorError("UNSUPPORTED_ROUTE", name)
        mapper.ts("integer")
        bindings[destination] = {"name": name, "type": "number", "literal": _js(name)}
    return bindings


def _dispatch_call(
    api: dict[str, Any] | None,
    paths: set[str],
    routes: dict[str, dict[str, str]],
    allowed: set[str],
) -> dict[str, Any] | None:
    if api is None:
        return None
    fields: list[str] = []
    used: list[dict[str, str]] = []
    reads_state = False
    for param in api["params"]:
        source = str(param["source"])
        expr = _state_expr(source, paths)
        if expr is None and source in allowed:
            route = routes.get(source)
            if route is not None:
                expr = f"action.{route['name']}"
                used.append(route)
        if expr is None:
            if param["optional"]:
                continue
            return None
        if expr.startswith("state"):
            reads_state = True
        fields.append(f"{prop(str(param['name']))}: {expr}")
    if not fields:
        snippet = f"{api['action']}()"
    elif len(fields) == 1:
        snippet = f"{api['action']}({{ {fields[0]} }})"
    else:
        body = ",\n          ".join(fields)
        snippet = f"{api['action']}({{\n          {body},\n        }})"
    return {"snippet": snippet, "routes": used, "reads_state": reads_state}


def _state_expr(source: str, paths: set[str]) -> str | None:
    if source not in paths:
        return None
    expr = "state"
    for part in source.split("."):
        if part == "":
            return None
        expr = ts_access(expr, part)
    return expr


def _models_context(
    header: str,
    feature: str,
    mapper: TypeMapper,
    apis: list[dict[str, Any]],
    model: dict[str, Any],
) -> dict[str, Any]:
    interfaces: list[dict[str, Any]] = []
    taken: set[str] = set()
    for name in mapper.fields:
        class_name = pascal(name)
        if class_name in taken:
            raise GeneratorError("UNSUPPORTED_NAME", name)
        taken.add(class_name)
        interfaces.append(
            {
                "name": class_name,
                "fields": mapper.interface_fields(name),
                "comment": "",
            }
        )
    for api in apis:
        comment = f"{api['purpose']} {api['method']} {api['endpoint']}"
        pairs = (
            (api["request_name"], _request_blocks(api["params"])),
            (api["response_name"], [f"  {field}" for field in api["response_fields"]]),
        )
        for name, fields in pairs:
            if not name:
                continue
            if name in taken:
                raise GeneratorError("UNSUPPORTED_NAME", name)
            taken.add(name)
            interfaces.append({"name": name, "fields": fields, "comment": comment})
    return {
        "header": header,
        "feature_key": feature,
        "interfaces": interfaces,
        "codes": _codes(model["codes"]),
        "errors": model["screen_errors"],
    }


def _request_blocks(params: list[dict[str, Any]]) -> list[str]:
    blocks: list[str] = []
    for param in params:
        blocks.append(f"  /** {param['comment']} */")
        blocks.append(f"  {param['decl']}")
    return blocks


def _codes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        code_id = str(row["code_id"])
        grouped.setdefault(code_id, []).append(
            {"key": prop(str(row["code"])), "value": _js(str(row["display_value"]))}
        )
    return [{"key": prop(code_id), "rows": items} for code_id, items in grouped.items()]


def _actions_context(
    header: str,
    slug: str,
    apis: list[dict[str, Any]],
    screen_label: str,
    initialize: str,
    rules: dict[str, Any] | None,
    init_routes: list[dict[str, str]],
) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    imports: list[str] = []
    if initialize:
        actions.append(
            {
                "var": initialize,
                "type": f"[{screen_label}] Initialize",
                "props": [
                    {"decl": f"{route['name']}: {route['type']};"} for route in init_routes
                ],
            }
        )
    if rules is not None:
        for setter in rules["setters"]:
            actions.append(
                {
                    "var": setter["name"],
                    "type": f"[{screen_label}] {setter['label']}",
                    "props": [{"decl": f"{setter['prop']}: {setter['type']};"}],
                }
            )
    for api in apis:
        props = [{"decl": param["decl"]} for param in api["params"]]
        actions.append(
            {
                "var": api["action"],
                "type": f"[{screen_label}] {api['action_label']}",
                "props": props,
            }
        )
        actions.append(
            {
                "var": api["success"],
                "type": f"[{screen_label}] {api['action_label']} Success",
                "props": [{"decl": f"body: {api['response_name']};"}],
            }
        )
        actions.append(
            {
                "var": api["failure"],
                "type": f"[{screen_label}] {api['action_label']} Failure",
                "props": [{"decl": "message: string;"}],
            }
        )
        imports.append(str(api["response_name"]))
    return {
        "header": header,
        "slug": slug,
        "actions": actions,
        "model_imports": imports,
    }


def _reducer_context(
    header: str,
    slug: str,
    feature: str,
    prefix: str,
    apis: list[dict[str, Any]],
    rules: dict[str, Any] | None,
) -> dict[str, Any]:
    cases: list[str] = []
    imported: list[str] = []
    response_imports: list[str] = []
    state_name = f"{prefix}State"
    if rules is not None:
        for setter in rules["setters"]:
            segments = str(setter["path"]).split(".")
            cases.append(
                render_prop_case(
                    str(setter["name"]),
                    state_name,
                    f"{{ {setter['prop']}: {setter['type']} }}",
                    [(segments, f"action.{setter['prop']}")],
                )
            )
            imported.append(str(setter["name"]))
    for api in apis:
        if not api["updates"]:
            continue
        cases.append(
            render_success_case(
                str(api["success"]),
                state_name,
                str(api["response_name"]),
                api["updates"],
            )
        )
        imported.append(str(api["success"]))
        response_imports.append(str(api["response_name"]))
    return {
        "header": header,
        "slug": slug,
        "feature_key": feature,
        "class_prefix": prefix,
        "cases": cases,
        "action_imports": imported,
        "model_imports": response_imports,
        "use_state_type": bool(cases),
    }


def _success_navigations(areas: list[dict[str, Any]]) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    for area in areas:
        for button in area["buttons"]:
            nav = button.get("navigate")
            if not nav:
                continue
            success = str(nav["success"])
            target = str(nav["target"])
            previous = seen.get(success)
            if previous is not None and previous != target:
                raise GeneratorError("UNSUPPORTED_NAVIGATION", success)
            if previous is None:
                seen[success] = target
                stem = success.removesuffix("Success")
                found.append(
                    {
                        "success": success,
                        "effect": f"navigateAfter{stem[:1].upper()}{stem[1:]}$",
                        "literal": _js(target),
                    }
                )
    return found


def _effects_context(
    header: str,
    slug: str,
    prefix: str,
    apis: list[dict[str, Any]],
    initialize: str,
    init_calls: list[str],
    navigations: list[dict[str, str]],
    init_routes: list[dict[str, str]],
    init_reads_state: bool,
    form_fills: dict[str, Any],
    mark_pristine: dict[str, Any] | None,
) -> dict[str, Any]:
    names: list[str] = []
    model_imports: list[str] = []
    if initialize:
        names.append(initialize)
    for api in apis:
        names.extend((str(api["action"]), str(api["success"]), str(api["failure"])))
        request_name = str(api["request_name"])
        response_name = str(api["response_name"])
        if request_name and request_name not in model_imports:
            model_imports.append(request_name)
        if response_name not in model_imports:
            model_imports.append(response_name)
    return {
        "header": header,
        "slug": slug,
        "class_name": f"{prefix}Effects",
        "class_prefix": prefix,
        "service_name": f"{prefix}ApiService",
        "apis": apis,
        "action_imports": names,
        "model_imports": model_imports,
        "initialize": initialize,
        "init_calls": init_calls,
        "navigations": navigations,
        "init_routes": init_routes,
        "init_reads_state": init_reads_state,
        "init_action_type": "{ "
        + "; ".join(f"{route['name']}: {route['type']}" for route in init_routes)
        + " }",
        "form_fills": form_fills["fills"],
        "form_class": _form_binding(form_fills, mark_pristine),
        "form_import": _form_binding_import(form_fills, mark_pristine),
        "mark_pristine": mark_pristine,
    }


def _form_binding(form_fills: dict[str, Any], mark_pristine: dict[str, Any] | None) -> str:
    filled = str(form_fills["class_name"])
    if mark_pristine is None:
        return filled
    pristine = str(mark_pristine["class_name"])
    if filled and filled != pristine:
        raise GeneratorError("UNSUPPORTED_ACTION", "FORM")
    return pristine


def _form_binding_import(
    form_fills: dict[str, Any],
    mark_pristine: dict[str, Any] | None,
) -> str:
    if mark_pristine is None:
        return str(form_fills["import"])
    return str(mark_pristine["import"])


def _form_fills(
    areas: list[dict[str, Any]],
    model: dict[str, Any],
    apis: list[dict[str, Any]],
) -> dict[str, Any]:
    controls = {str(row["field_id"]) for row in model["inputs"]}
    responses: dict[tuple[str, str], str] = {}
    for row in model["responses"]:
        responses[(str(row["api_id"]), str(row["field"]))] = str(row["data_type"])
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in model["response_mappings"]:
        destination = str(row["destination"])
        if not destination.startswith("input."):
            continue
        control = destination.removeprefix("input.")
        field = str(row["response_field"])
        if (
            control not in controls
            or not IDENT.fullmatch(control)
            or not IDENT.fullmatch(field)
            or responses.get((str(row["api_id"]), field)) != "string"
        ):
            raise GeneratorError("UNSUPPORTED_STATE", destination)
        pairs = grouped.setdefault(str(row["api_id"]), [])
        if any(item["control"] == control for item in pairs):
            raise GeneratorError("UNSUPPORTED_STATE", destination)
        pairs.append({"control": control, "field": field})
    empty = {"fills": [], "class_name": "", "import": ""}
    if not grouped:
        return empty
    owners = [area for area in areas if area.get("form_context")]
    if len(owners) != 1:
        raise GeneratorError("UNSUPPORTED_STATE", "input")
    owner = owners[0]
    by_api = {str(api["api_id"]): api for api in apis}
    fills: list[dict[str, Any]] = []
    for api_id, pairs in grouped.items():
        api = by_api.get(api_id)
        if api is None:
            raise GeneratorError("UNSUPPORTED_STATE", api_id)
        action = str(api["action"])
        fills.append(
            {
                "success": str(api["success"]),
                "response_name": str(api["response_name"]),
                "effect": f"fill{action[:1].upper()}{action[1:]}$",
                "assignments": pairs,
            }
        )
    module_import = str(owner["form_module_import"])
    return {
        "fills": fills,
        "class_name": str(owner["form_class"]),
        "import": "../" + module_import.removeprefix("./"),
    }


def _mark_pristine(
    areas: list[dict[str, Any]],
    model: dict[str, Any],
    apis: list[dict[str, Any]],
    url: str,
    mapper: TypeMapper,
) -> dict[str, Any] | None:
    steps = [step for step in model["initialization"] if str(step["operation"]) == "MARK_PRISTINE"]
    if not steps:
        return None
    if len(steps) != 1:
        raise GeneratorError("UNSUPPORTED_ACTION", "MARK_PRISTINE")
    step = steps[0]
    if str(step["condition"]) != "ALWAYS" or str(step["reference"]) != "FORM":
        raise GeneratorError("UNSUPPORTED_ACTION", str(step["init_id"]))
    raw = str(step["depends_on"]).strip()
    if raw == "NONE":
        raise GeneratorError("UNSUPPORTED_ACTION", str(step["init_id"]))
    by_init = {str(row["init_id"]): row for row in model["initialization"]}
    by_api = {str(api["api_id"]): api for api in apis}
    routes = _route_binding(model, url, mapper)
    paths = {str(row["state_path"]) for row in model["state_types"]}
    successes: list[str] = []
    failures: list[str] = []
    for dep_id in raw.split(","):
        parent = by_init.get(dep_id.strip())
        if (
            parent is None
            or str(parent["condition"]) != "ALWAYS"
            or str(parent["operation"]) != "CALL_API"
        ):
            raise GeneratorError("UNSUPPORTED_ACTION", str(step["init_id"]))
        api = by_api.get(str(parent["reference"]))
        allowed = _route_allowed(parent, by_init, model)
        if _dispatch_call(api, paths, routes, allowed) is None:
            raise GeneratorError("UNSUPPORTED_ACTION", str(step["init_id"]))
        successes.append(str(api["success"]))
        failures.append(str(api["failure"]))
    owners = [area for area in areas if area.get("form_context")]
    if len(owners) != 1 or not successes:
        raise GeneratorError("UNSUPPORTED_ACTION", "FORM")
    module_import = str(owners[0]["form_module_import"])
    return {
        "successes": successes,
        "failures": failures,
        "class_name": str(owners[0]["form_class"]),
        "import": "../" + module_import.removeprefix("./"),
    }


def _selector_context(
    header: str,
    slug: str,
    feature: str,
    prefix: str,
    state: SBranch,
) -> dict[str, Any]:
    leaves: list[dict[str, str]] = []
    used: set[str] = set()
    for path in iter_leaves(state):
        name = "select" + "".join(pascal(part) for part in path)
        if name in used:
            raise GeneratorError("UNSUPPORTED_NAME", name)
        used.add(name)
        expr = "state"
        for part in path:
            expr = ts_access(expr, part)
        leaves.append({"name": name, "expr": expr})
    return {
        "header": header,
        "slug": slug,
        "feature_key": feature,
        "class_prefix": prefix,
        "leaves": leaves,
    }


def _service_context(
    header: str,
    slug: str,
    prefix: str,
    apis: list[dict[str, Any]],
) -> dict[str, Any]:
    methods: list[dict[str, Any]] = []
    imports: list[str] = []
    use_params = False
    for api in apis:
        if api["query_params"]:
            use_params = True
        methods.append(
            {
                "signature": _signature(api),
                "lines": _method_lines(api),
            }
        )
        if api["request_name"]:
            imports.append(str(api["request_name"]))
        imports.append(str(api["response_name"]))
    return {
        "header": header,
        "slug": slug,
        "class_name": f"{prefix}ApiService",
        "methods": methods,
        "model_imports": imports,
        "use_http": bool(apis),
        "use_params": use_params,
        "use_observable": bool(apis),
    }


def _signature(api: dict[str, Any]) -> str:
    response = api["response_name"]
    if api["has_request"]:
        return f"{api['method_name']}(request: {api['request_name']}): Observable<{response}>"
    return f"{api['method_name']}(): Observable<{response}>"


def _method_lines(api: dict[str, Any]) -> list[str]:
    keyword = "let" if api["path_params"] else "const"
    lines = [f"{keyword} url = {_js(str(api['endpoint']))};"]
    for param in api["path_params"]:
        token = "{" + str(param["name"]) + "}"
        lines.append(
            "url = url.split("
            + _js(token)
            + ").join(encodeURIComponent(String(request"
            + str(param["member"])
            + ")));"
        )
    if api["query_params"]:
        lines.append("let params = new HttpParams();")
        for param in api["query_params"]:
            assignment = (
                "params = params.set("
                + _js(str(param["name"]))
                + ", String(request"
                + str(param["member"])
                + "));"
            )
            if param["optional"]:
                lines.append(f"if (request{param['member']} !== undefined) {{")
                lines.append(f"  {assignment}")
                lines.append("}")
            else:
                lines.append(assignment)
    if api["body_params"]:
        lines.append("const body = {")
        for param in api["body_params"]:
            lines.append(f"  {prop(str(param['name']))}: request{param['member']},")
        lines.append("};")
    lines.append(f"return {_http_call(api)};")
    return lines


def _http_call(api: dict[str, Any]) -> str:
    call = f"this.http.{api['http']}<{api['response_name']}>"
    has_query = bool(api["query_params"])
    has_body = bool(api["body_params"])
    if api["http"] == "get":
        if has_query:
            return f"{call}(url, {{ params }})"
        return f"{call}(url)"
    if api["http"] == "delete":
        options: list[str] = []
        if has_query:
            options.append("params")
        if has_body:
            options.append("body")
        if options:
            return f"{call}(url, {{ {', '.join(options)} }})"
        return f"{call}(url)"
    body = "body" if has_body else "{}"
    if has_query:
        return f"{call}(url, {body}, {{ params }})"
    return f"{call}(url, {body})"


def _steps_context(
    header: str,
    feature: str,
    meta: dict[str, Any],
    model: dict[str, Any],
) -> dict[str, Any]:
    return {
        "header": header,
        "feature_key": feature,
        "screen_type": str(meta["screen_type"]),
        "screen_url": str(meta["url"]),
        "initialization": model["initialization"],
        "events": model["events"],
        "event_steps": model["event_steps"],
        "navigation": model["navigation"],
        "defaults": model["defaults"],
    }


def _module_context(
    header: str,
    slug: str,
    feature: str,
    prefix: str,
    areas: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "header": header,
        "slug": slug,
        "feature_key": feature,
        "class_name": f"{prefix}Module",
        "screen_class": f"{prefix}ScreenComponent",
        "reducer_name": f"{feature}Reducer",
        "effects_name": f"{prefix}Effects",
        "service_name": f"{prefix}ApiService",
        "areas": areas,
        "form_class": next(
            (str(area["form_class"]) for area in areas if area["form_context"]),
            "",
        ),
        "form_import": next(
            (str(area["form_module_import"]) for area in areas if area["form_context"]),
            "",
        ),
    }


def _js(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)
