# Generation Report（Phase 1）

対象は `toolchain/models/list-screen-spec.json`（画面 ID `SCR-001`、製品一覧、LIST、`/products`）。Python 3.13.12 で実行した。

## 実行結果

pytest は `tests/generator` で 19 件成功。ruff は `generator` と `tests` で指摘なし。

`generate` は 18 ファイルを `generated/product-list/` に作成した。

| 状態 | パス |
| --- | --- |
| CREATE | `generated/product-list/models/product-list.models.ts` |
| CREATE | `generated/product-list/store/product-list.state.ts` |
| CREATE | `generated/product-list/store/product-list.actions.ts` |
| CREATE | `generated/product-list/store/product-list.reducer.ts` |
| CREATE | `generated/product-list/store/product-list.effects.ts` |
| CREATE | `generated/product-list/store/product-list.selectors.ts` |
| CREATE | `generated/product-list/services/product-list-api.service.ts` |
| CREATE | `generated/product-list/product-list.steps.ts` |
| CREATE | `generated/product-list/query/product-list-query.form.ts` |
| CREATE | `generated/product-list/query/product-list-query.component.ts` |
| CREATE | `generated/product-list/query/product-list-query.component.html` |
| CREATE | `generated/product-list/actions/product-list-actions.component.ts` |
| CREATE | `generated/product-list/actions/product-list-actions.component.html` |
| CREATE | `generated/product-list/list/product-list-list.component.ts` |
| CREATE | `generated/product-list/list/product-list-list.component.html` |
| CREATE | `generated/product-list/product-list.component.ts` |
| CREATE | `generated/product-list/product-list.component.html` |
| CREATE | `generated/product-list/product-list.module.ts` |

今回の generate では、一覧 18 ファイルに加え、登録 16、更新 16、詳細 15 ファイルも `generated/` に書いた。

## 一覧画面で生成した内容

- 名前付き型 `ProductSummary`、`StatusOption`
- `API-001` `GET /api/products/`。応答型は `ProductListResponse`。query は `name`、`status`、`page`、`page_size`、`ordering`。任意の `name` と `status` は未指定なら送らない
- `API-002` `GET /api/products/options/`。応答型は `ProductStatusOptionsResponse`
- 成功時の代入: `results` → `list.items`、`count` → `pagination.total`、`statuses` → `options["OPT-001"]`
- コード `CODE-001`（`new` = 新規、`closed` = 完了）と画面エラー `ERR-001`
- 初期化、イベント、操作順、遷移 `NAV-001` → `/products/new`、入力初期値 `EMPTY` を steps 定数として転記
- 画面を開くと `initializeProductList` を送る。Effect は `getProductStatusOptions` と、state の `page` / `pageSize` / `ordering` を渡す `getProductList` を呼ぶ。`query.applied` は渡さない
- 検索結果コンポーネントは `list.items` を表にする。状態は `CODE-001` の表示名、空値は `-`
- 検索条件は製品名と状態。状態の候補は `options.OPT-001`。検索ボタンは入力チェックのあと `productList` を送る。製品名が 100 文字を超える、または状態が候補に無いときは API を呼ばない
- 空の製品名と状態は query に載せない。検索はページを `1` に戻してから一覧を取る。初期 state はページ `1`、件数 `20`、ソート `updated_at DESC`
- 一覧のページ、表示件数（`20`、`50`、`100`）、ソートを変えると一覧を取り直す。件数とソートの変更はページを `1` に戻す
- 新規登録ボタンは `/products/new` へ遷移する。渡すパラメータは無い
- 一覧取得が成功して結果が 0 件のとき「データがありません」を出す。成功前の空配列では出さない
- 画面コンポーネント `ProductListScreenComponent` を module が export する

Service 以外に `HttpClient` は出ていない。コンポーネントは `standalone: false`。生成 TypeScript に `any` は使っていない。

## 検証の境界

この JSON 単体を既存の `toolchain/validate_json.py` に渡すと、`NAV003`（遷移先 `/products/new` が同一セットに無い）で失敗する。4 画面をまとめて渡すとエラーは 0 件だった。

Generator は Schema と `validate_model` を通過した JSON だけを生成する。1 ファイルの CLI では `validate_project` を適用しない。`/products/new` の画面は作っていない。

## 残課題

初期表示、検索、ページ操作、登録フォームの保存、登録の二重送信防止、詳細と更新の初期表示、一覧と詳細から編集への遷移、更新フォームの未変更化、検索と更新の通信中のボタン無効化、4画面のURLルート、`AppModule` の起動まで動く。次工程で扱うもの:

- `APPLY_DEFAULTS` の実行。フォームの初期値は空のまま。`route` の同名項目以外のパラメータ付き遷移は未実行
- 検索条件はフォームにあり、store には置いていない。登録の `input` はフォームから body へ送る。詳細と更新の `route.id` は画面 URL から読む。更新の取得結果は製品名と状態の入力へ入れる。更新ボタンはチェック後に `PATCH` し、成功後に一覧へ戻る
- 読み込み中と通信失敗を保持する state。`state_types` に項目が無いので追加していない。失敗アクションは payload の `message` だけを持つ
- 権限制御。登録以外の二重操作防止
- API のベース URL。JSON にあるのはパスだけなので、Service はそのパスをそのまま使う
- Feature module ごとの `provideHttpClient()`。ホストで 1 回だけ提供する形への整理
