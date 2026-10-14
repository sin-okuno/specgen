from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest
from generator.cli import main
from generator.engine import generate_to, render_plan
from generator.errors import GeneratorError
from generator.host import render_host
from generator.loader import load_model
from generator.naming import (
    action_label,
    api_type_stem,
    camel,
    file_slug,
    pascal,
    prop,
    screen_stem,
)
from generator.planner import build_plan
from generator.types import TypeMapper

ROOT = Path(__file__).resolve().parents[2]
LIST = ROOT / "toolchain" / "models" / "list-screen-spec.json"
MODELS = ROOT / "toolchain" / "models"
EXPECTED = [
    "product-list/models/product-list.models.ts",
    "product-list/store/product-list.state.ts",
    "product-list/store/product-list.actions.ts",
    "product-list/store/product-list.reducer.ts",
    "product-list/store/product-list.effects.ts",
    "product-list/store/product-list.selectors.ts",
    "product-list/services/product-list-api.service.ts",
    "product-list/product-list.steps.ts",
    "product-list/query/product-list-query.form.ts",
    "product-list/query/product-list-query.component.ts",
    "product-list/query/product-list-query.component.html",
    "product-list/actions/product-list-actions.component.ts",
    "product-list/actions/product-list-actions.component.html",
    "product-list/list/product-list-list.component.ts",
    "product-list/list/product-list-list.component.html",
    "product-list/product-list.component.ts",
    "product-list/product-list.component.html",
    "product-list/product-list.module.ts",
]


def test_load_valid_model() -> None:
    document = load_model(LIST)
    assert document["metadata"]["screen_id"] == "SCR-001"
    assert document["schema_version"] == "0.3"


def test_reject_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(GeneratorError) as caught:
        load_model(path)
    assert caught.value.code == "INVALID_JSON"


def test_reject_schema_violation(tmp_path: Path) -> None:
    path = tmp_path / "empty.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(GeneratorError) as caught:
        load_model(path)
    assert caught.value.code == "SCHEMA"


def test_naming_conversion() -> None:
    assert pascal("SCR-001") == "Scr001"
    assert camel("SCR-001") == "scr001"
    assert file_slug("SCR-001") == "scr-001"
    assert pascal("productSummary") == "ProductSummary"
    assert pascal("statusOption") == "StatusOption"
    assert pascal("API-001") == "Api001"
    assert camel("API-001") == "api001"
    assert file_slug("API-001") == "api-001"
    assert pascal("OPT-001") == "Opt001"
    assert prop("pageSize") == "pageSize"
    assert prop("OPT-001") == '"OPT-001"'
    assert api_type_stem("/api/products/", "一覧取得") == "ProductList"
    assert api_type_stem("/api/products/options/", "状態候補取得") == "ProductStatusOptions"
    assert api_type_stem("/api/products/{id}/", "詳細取得") == "ProductDetail"
    assert action_label("ProductList") == "Product List"
    assert action_label("ProductStatusOptions") == "Product Status Options"
    assert screen_stem("製品一覧") == "ProductList"
    assert file_slug("ProductList") == "product-list"


def test_type_mapping() -> None:
    mapper = TypeMapper(["productSummary", "statusOption"], [])
    assert mapper.ts("string") == "string"
    assert mapper.ts("integer") == "number"
    assert mapper.ts("number") == "number"
    assert mapper.ts("boolean") == "boolean"
    assert mapper.ts("date") == "string"
    assert mapper.ts("datetime") == "string"
    assert mapper.ts("string[]") == "string[]"
    assert mapper.ts("integer[]") == "number[]"
    assert mapper.ts("productSummary") == "ProductSummary"
    assert mapper.ts("productSummary[]") == "ProductSummary[]"
    assert mapper.ts("statusOption[]", nullable=True) == "StatusOption[] | null"


def test_reject_unsupported_type() -> None:
    mapper = TypeMapper(["productSummary"], [])
    for data_type in ("object", "object[]", "nope", "nope[]", "string[][]"):
        with pytest.raises(GeneratorError) as caught:
            mapper.ts(data_type)
        assert caught.value.code == "UNSUPPORTED_TYPE"


def test_reject_unsupported_type_in_model(tmp_path: Path) -> None:
    document = copy.deepcopy(load_model(LIST))
    document["model"]["state_types"].append(
        {
            "line": 1,
            "state_path": "note.text",
            "data_type": "object",
            "nullable": "No",
        }
    )
    path = tmp_path / "unsupported.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(GeneratorError) as caught:
        build_plan(load_model(path))
    assert caught.value.code == "UNSUPPORTED_TYPE"


def test_reject_unsupported_operation(tmp_path: Path) -> None:
    document = copy.deepcopy(load_model(LIST))
    document["model"]["event_steps"][0]["operation"] = "DROP_TABLE"
    path = tmp_path / "operation.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(GeneratorError) as caught:
        build_plan(load_model(path))
    assert caught.value.code == "UNSUPPORTED_OPERATION"


def test_plan_file_list() -> None:
    plan = build_plan(load_model(LIST))
    assert [item.relative_path for item in plan.files] == EXPECTED
    assert [item.template for item in plan.files] == [
        "models.ts.j2",
        "state.ts.j2",
        "actions.ts.j2",
        "reducer.ts.j2",
        "effects.ts.j2",
        "selectors.ts.j2",
        "api.service.ts.j2",
        "steps.ts.j2",
        "query.form.ts.j2",
        "component.ts.j2",
        "component.html.j2",
        "component.ts.j2",
        "component.html.j2",
        "component.ts.j2",
        "component.html.j2",
        "screen.component.ts.j2",
        "screen.component.html.j2",
        "module.ts.j2",
    ]
    module = plan.files[-1]
    assert "product-list/services/product-list-api.service.ts" in module.depends


def test_all_example_models_plan() -> None:
    for path in sorted(MODELS.glob("*-screen-spec.json")):
        plan = build_plan(load_model(path))
        rendered = dict(render_plan(plan))
        assert rendered
        for relative, content in rendered.items():
            if relative.endswith((".ts", ".html")):
                assert not re.search(r"\bany\b", content), relative


def test_list_render_uses_declared_model() -> None:
    rendered = dict(render_plan(build_plan(load_model(LIST))))
    models = rendered["product-list/models/product-list.models.ts"]
    assert "export interface ProductSummary" in models
    assert "export interface ProductListResponse" in models
    assert "export interface ProductStatusOptionsResponse" in models
    assert "Api001Response" not in models
    assert "export interface StatusOption" in models
    assert "データがありません" in models
    service = rendered["product-list/services/product-list-api.service.ts"]
    assert 'const url = "/api/products/"' in service
    assert "getProductList(" in service
    assert "this.http.get<ProductListResponse>" in service
    assert "api001" not in service
    assert "SCR-001" not in service
    assert "API-001" not in service
    query = rendered["product-list/query/product-list-query.component.ts"]
    assert "HttpClient" not in query
    assert "standalone: false" in query
    assert "scr-001" not in query
    reducer = rendered["product-list/store/product-list.reducer.ts"]
    assert "items: action.body.results" in reducer
    assert '"OPT-001": action.body.statuses' in reducer
    module = rendered["product-list/product-list.module.ts"]
    assert "StoreModule.forFeature" in module
    assert "EffectsModule.forFeature" in module
    assert "ReactiveFormsModule" in module
    steps = rendered["product-list/product-list.steps.ts"]
    assert '"VALIDATE"' in steps
    assert '"/products/new"' in steps
    actions = rendered["product-list/store/product-list.actions.ts"]
    assert "export const productList = createAction(" in actions
    assert '"[Product List] Product List"' in actions
    assert '"[Product List] Product List Success"' in actions
    assert '"[Product List] Product Status Options"' in actions
    assert "Call API-001" not in actions
    assert "[SCR-001]" not in actions
    assert "productListSuccess" in rendered["product-list/store/product-list.effects.ts"]
    selectors = rendered["product-list/store/product-list.selectors.ts"]
    assert "(state: ProductListState)" in selectors
    assert "(state) =>" not in selectors
    assert "export const initializeProductList = createAction(" in actions
    assert '"[Product List] Initialize"' in actions
    effects = rendered["product-list/store/product-list.effects.ts"]
    assert "initializeProductList$" in effects
    assert "productStatusOptions()" in effects
    assert "page: state.pagination.page" in effects
    assert "page_size: state.pagination.pageSize" in effects
    assert "ordering: state.sort.ordering" in effects
    assert "query.applied" not in effects
    assert "page: 1" not in effects
    listing = rendered["product-list/list/product-list-list.component.html"]
    assert "製品名" in listing
    assert "item.name" in listing
    assert 'codeLabel("CODE-001", item.status, "-")' in listing
    assert 'openRow(item.id)' in listing
    assert 'openRowEdit(item.id, $event)' in listing
    assert 'aria-label="編集"' in listing
    assert "listReceived() && items().length === 0" in listing
    assert "データがありません" in listing
    listing_ts = rendered["product-list/list/product-list-list.component.ts"]
    assert "listReceived = signal(false)" in listing_ts
    assert "ofType(productListSuccess)" in listing_ts
    assert 'navigateByUrl("/products" + "/" + encodeURIComponent(String(id)))' in listing_ts
    assert '"/products" + "/" + encodeURIComponent(String(id)) + "/edit"' in listing_ts
    screen = rendered["product-list/product-list.component.ts"]
    assert "initializeProductList()" in screen
    assert "ProductListScreenComponent" in module
    assert "exports: [ProductListScreenComponent]" in module
    form = rendered["product-list/query/product-list-query.form.ts"]
    assert "100文字以内で入力してください" in form
    assert "有効な状態を選択してください" in form
    assert "value.productName.length > 100" in form
    query_html = rendered["product-list/query/product-list-query.component.html"]
    assert 'formControlName="productName"' in query_html
    assert 'formControlName="status"' in query_html
    assert "optionsOpt001()" in query_html
    actions_html = rendered["product-list/actions/product-list-actions.component.html"]
    assert "検索" in actions_html
    assert "searchButtonDisabled()" in actions_html
    assert "新規登録" in actions_html
    assert '<button type="button" (click)="createButton()">新規登録</button>' in actions_html
    actions_ts = rendered["product-list/actions/product-list-actions.component.ts"]
    assert "queryForm.validate(this.optionsOpt001())" in actions_ts
    assert "productList(request)" in actions_ts
    assert "page: 1," in actions_ts
    assert "setPaginationPage({ page: 1 })" in actions_ts
    assert "applyQuery()" in actions_ts
    assert "page_size: state.pagination.pageSize" in actions_ts
    assert 'if (value.productName !== "")' in actions_ts
    assert 'this.router.navigateByUrl("/products/new")' in actions_ts
    assert "searchButtonLoading()" in actions_ts
    assert "ofType(productList)," in actions_ts
    assert "ofType(productListSuccess, productListFailure)" in actions_ts
    state = rendered["product-list/store/product-list.state.ts"]
    assert "page: 1," in state
    assert "pageSize: 20," in state
    assert 'ordering: "updated_at DESC",' in state
    listing_ts = rendered["product-list/list/product-list-list.component.ts"]
    assert "changePaginationPageSize" in listing_ts
    assert "changeSortOrdering" in listing_ts
    assert "pageSizes" in listing_ts
    assert "20, 50, 100" in listing_ts
    assert "ProductListQueryForm" in module


def test_detail_named_type_initial() -> None:
    path = MODELS / "detail-screen-spec.json"
    rendered = dict(render_plan(build_plan(load_model(path))))
    state = rendered["product-detail/store/product-detail.state.ts"]
    assert "product: ProductDetail;" in state
    assert "manufacturer:" in state
    service = rendered["product-detail/services/product-detail-api.service.ts"]
    assert "encodeURIComponent" in service
    effects = rendered["product-detail/store/product-detail.effects.ts"]
    assert "initializeProductDetail$" in effects
    assert "productDetail({ id: action.id })" in effects
    screen = rendered["product-detail/product-detail.component.ts"]
    assert 'paramMap.get("id")' in screen
    assert "initializeProductDetail({\n      id: Number(id),\n    })" in screen
    detail_view = rendered["product-detail/detail/product-detail-detail.component.html"]
    assert "製品名" in detail_view
    assert "メーカー名" in detail_view
    assert 'product().manufacturer.name === ""' in detail_view
    detail_ts = rendered["product-detail/detail/product-detail-detail.component.ts"]
    assert "selectDataProduct" in detail_ts
    assert 'codeLabel("CODE-001", product().status, "-")' in detail_view
    detail_actions = rendered["product-detail/actions/product-detail-actions.component.ts"]
    assert 'navigateByUrl("/products")' in detail_actions
    assert "{id}" not in detail_actions
    assert 'paramMap.get("id")' in detail_actions
    assert 'encodeURIComponent(id) + "/edit"' in detail_actions
    detail_html = rendered["product-detail/actions/product-detail-actions.component.html"]
    assert "編集" in detail_html


def test_create_post_body() -> None:
    path = MODELS / "create-screen-spec.json"
    rendered = dict(render_plan(build_plan(load_model(path))))
    service = rendered["product-registration/services/product-registration-api.service.ts"]
    assert "this.http.post<ProductRegistrationResponse>" in service
    form = rendered["product-registration/form/product-registration-form.form.ts"]
    assert "製品名を1〜100文字で入力してください" in form
    assert "状態を選択してください" in form
    assert "isValid(optionsOpt001: readonly StatusOption[])" in form
    form_html = rendered["product-registration/form/product-registration-form.component.html"]
    assert 'formControlName="productName"' in form_html
    assert 'formControlName="status"' in form_html
    actions_html = rendered[
        "product-registration/actions/product-registration-actions.component.html"
    ]
    assert "保存" in actions_html
    assert "saveButtonDisabled()" in actions_html
    assert "キャンセル" in actions_html
    registration_actions = rendered[
        "product-registration/actions/product-registration-actions.component.ts"
    ]
    assert "queryForm.validate(this.optionsOpt001())" in registration_actions
    assert "input.productName" in registration_actions
    assert "input.status" in registration_actions
    assert "productRegistration(request)" in registration_actions
    assert "saveButtonSubmitting()" in registration_actions
    assert "saveButtonSubmitting.set(true)" in registration_actions
    assert "ofType(productRegistrationSuccess, productRegistrationFailure)" in registration_actions
    assert "saveButtonLoading" not in registration_actions
    assert 'navigateByUrl("/products")' in registration_actions
    effects = rendered["product-registration/store/product-registration.effects.ts"]
    assert "initializeProductRegistration$" in effects
    assert "productStatusOptions()" in effects
    assert "navigateAfterProductRegistration$" in effects
    assert "productRegistrationSuccess" in effects
    assert 'navigateByUrl("/products")' in effects
    module = rendered["product-registration/product-registration.module.ts"]
    assert "ProductRegistrationForm" in module


def test_edit_patch() -> None:
    path = MODELS / "edit-screen-spec.json"
    rendered = dict(render_plan(build_plan(load_model(path))))
    service = rendered["product-update/services/product-update-api.service.ts"]
    assert "this.http.patch<ProductUpdateResponse>" in service
    effects = rendered["product-update/store/product-update.effects.ts"]
    assert "initializeProductUpdate$" in effects
    assert "productStatusOptions()" in effects
    assert "productDetail({ id: action.id })" in effects
    assert "productName: action.body.name" in effects
    assert "status: action.body.status" in effects
    assert "markFormPristine$" in effects
    assert "form.markAsPristine()" in effects
    assert "ofType(productDetailSuccess)" in effects
    assert "ofType(productStatusOptionsSuccess)" in effects
    assert "ofType(productDetailFailure, productStatusOptionsFailure)" in effects
    assert "navigateAfterProductUpdate$" in effects
    assert 'navigateByUrl("/products")' in effects
    screen = rendered["product-update/product-update.component.ts"]
    assert 'paramMap.get("id")' in screen
    reducer = rendered["product-update/store/product-update.reducer.ts"]
    assert "input:" not in reducer
    update_html = rendered["product-update/actions/product-update-actions.component.html"]
    assert "更新" in update_html
    assert "saveButtonDisabled()" in update_html
    update_actions = rendered["product-update/actions/product-update-actions.component.ts"]
    assert "saveButtonLoading()" in update_actions
    assert "productUpdate(request)" in update_actions
    assert "input.productName" in update_actions
    assert "input.status" in update_actions
    assert 'paramMap.get("id")' in update_actions
    assert "Submitting" not in update_actions
    assert "ofType(productUpdate)," in update_actions
    assert "ofType(productUpdateSuccess, productUpdateFailure)" in update_actions
    update_form = rendered["product-update/form/product-update-form.component.html"]
    assert 'formControlName="productName"' in update_form


def test_dry_run_creates_nothing(tmp_path: Path) -> None:
    output = tmp_path / "generated"
    results = generate_to(LIST, output, dry_run=True)
    assert results
    assert all(item.status == "CREATE" for item in results)
    assert not output.exists()


def test_same_input_same_output(tmp_path: Path) -> None:
    first = tmp_path / "a"
    second = tmp_path / "b"
    generate_to(LIST, first)
    generate_to(LIST, second)
    files_a = {
        path.relative_to(first): path.read_bytes() for path in first.rglob("*") if path.is_file()
    }
    files_b = {
        path.relative_to(second): path.read_bytes()
        for path in second.rglob("*")
        if path.is_file()
    }
    assert files_a == files_b
    again = dict(render_plan(build_plan(load_model(LIST))))
    assert again == dict(render_plan(build_plan(load_model(LIST))))


def test_does_not_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "generated"
    generate_to(LIST, output)
    target = output / "product-list" / "models" / "product-list.models.ts"
    target.write_bytes(b"changed\n")
    with pytest.raises(GeneratorError) as caught:
        generate_to(LIST, output)
    assert caught.value.code == "OVERWRITE"
    assert target.read_bytes() == b"changed\n"


def test_identical_file_is_unchanged(tmp_path: Path) -> None:
    output = tmp_path / "generated"
    generate_to(LIST, output)
    second = generate_to(LIST, output)
    assert {item.status for item in second} == {"UNCHANGED"}


def test_host_routes_screens() -> None:
    models = sorted(MODELS.glob("*-screen-spec.json"))
    rendered = dict(render_host([load_model(path) for path in models]))
    module = rendered["app/app.module.ts"]
    new_at = module.index("component: ProductRegistrationScreenComponent")
    edit_at = module.index("component: ProductUpdateScreenComponent")
    detail_at = module.index("component: ProductDetailScreenComponent")
    assert 'path: "products/new"' in module
    assert 'path: "products/:id/edit"' in module
    assert 'path: "products/:id", component: ProductDetailScreenComponent' in module
    assert 'path: "products", component: ProductListScreenComponent' in module
    assert new_at < detail_at
    assert edit_at < detail_at
    assert "pathMatch: \"full\"" in module
    assert "ProductListScreenComponent" in module
    assert "ProductRegistrationScreenComponent" in module
    assert "ProductUpdateScreenComponent" in module
    assert "ProductDetailScreenComponent" in module
    assert "RouterModule.forRoot" in module
    assert "<router-outlet></router-outlet>" in rendered["app/app.component.html"]
    assert "selector: \"app-root\"" in rendered["app/app.component.ts"]


def test_host_rejects_duplicate_url() -> None:
    first = load_model(LIST)
    second = copy.deepcopy(first)
    second["metadata"]["screen_name"] = "製品詳細"
    with pytest.raises(GeneratorError) as caught:
        render_host([first, second])
    assert caught.value.code == "UNSUPPORTED_ROUTE"


def test_cli_plan_and_dry_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["plan", "--model", str(LIST)]) == 0
    planned = capsys.readouterr().out
    assert "product-list/models/product-list.models.ts" in planned
    assert "template: models.ts.j2" in planned
    output = tmp_path / "generated"
    assert main(["generate", "--model", str(LIST), "--output", str(output), "--dry-run"]) == 0
    dry = capsys.readouterr().out
    assert "CREATE" in dry
    assert "export interface ProductSummary" in dry
    assert not output.exists()
    assert main(["generate", "--model", str(LIST), "--output", str(output)]) == 0
    assert (output / "product-list" / "product-list.module.ts").is_file()
