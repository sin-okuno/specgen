# Screen Generator Phase 1 設計

Phase 1 は、共通 Markdown 画面仕様書 v1.5 から作られた Screen Model JSON を入力にして、Angular 22 の NgModule / NgRx / Service の土台を決定論的に出す。画面の完成、既存アプリへの組み込み、`ng build` は次工程である。

## パスの対応

指示書のパスと、このリポジトリの実体は次のとおり。

| 指示 | 実体 |
| --- | --- |
| `specification/SPECIFICATION_V1.5.md` | `SPECIFICATION_V1.5.md` |
| `specification/examples/*.md` | 正本は `examples/*.md`。`toolchain/examples/` は検証用の複製 |
| `toolchain/parser.py` | 同じ |
| `toolchain/model_validator.py` | 同じ |
| `toolchain/pipeline.py` | 同じ |
| `toolchain/screen-model.schema.json` | 同じ |
| `toolchain/models/list-screen-spec.json` | 同じ。リポジトリ直下の `models/` も同一内容 |

Parser、Validator、v1.5 仕様書、examples は変更していない。

## 責務

| モジュール | 役割 |
| --- | --- |
| `generator/loader.py` | JSON の読み込み。JSON Schema Draft 2020-12 と既存の `validate_model` を通す |
| `generator/naming.py` | 画面 ID や型名を Angular の識別子へ変換する |
| `generator/types.py` | 仕様の型を TypeScript 型へ変換する |
| `generator/planner.py` | 生成ファイル、テンプレート、依存関係を決める |
| `generator/renderer.py` | Jinja2 でレンダリングする |
| `generator/writer.py` | 出力ディレクトリの外へ出ない書き込み。既定では上書きしない |
| `generator/cli.py` | `plan` と `generate` |

Markdown は再解析しない。JSON を作る処理は既存 Parser のままである。

## 検証

1 ファイルに対して次を行う。

- `json.loads` に失敗したら `INVALID_JSON`
- `toolchain/screen-model.schema.json` に失敗したら `SCHEMA`
- `validate_model` がエラーを返したら `MODEL`

いずれかで失敗した JSON からはファイルを作らない。

`validate_project` は画面セット全体の URL 重複と遷移先の存在を見る。`list-screen-spec.json` だけを渡すと、遷移先 `/products/new` がセット内に無く `NAV003` になる。4 画面をまとめて既存の `validate_json.py` に渡すとエラーは 0 件である。Phase 1 の CLI は `--model` が 1 ファイルなので、画面間チェックは適用しない。遷移先は steps の定数として転記し、遷移先画面のコードは作らない。

## 命名

画面のファイル名とクラス名は画面名から作る。機能 ID は生成コードの名前、ファイル名、コメントに使わない。steps の値は仕様書の項目をそのまま転記する。

| 入力 | 結果 |
| --- | --- |
| 画面名「製品一覧」 | ディレクトリ `product-list`、クラス `ProductList`、feature key `productList` |
| `productSummary` | 型名 `ProductSummary` |
| `GET /api/products/` 用途「一覧取得」 | 型 `ProductListRequest` / `ProductListResponse`。Service メソッド `getProductList`。アクション `productList` / `productListSuccess` / `productListFailure`。型文字列は `[Product List] Product List` |
| `GET /api/products/options/` 用途「状態候補取得」 | 型 `ProductStatusOptionsResponse`。メソッド `getProductStatusOptions`。アクション `productStatusOptions` |
| `OPT-001` | state のプロパティ `"OPT-001"`。これは仕様の状態パスであり、ファイル名には使わない |
| `pageSize` | そのまま `pageSize` |

API のパラメータ名は通信上の名前のままにする。`page_size` を `pageSize` に変えない。

画面名の対応は「製品一覧」が `ProductList`、「製品登録」が `ProductRegistration`、「製品更新」が `ProductUpdate`、「製品詳細」が `ProductDetail` である。応答型と要求型の名前は、パスの先頭リソースと API の用途から作る。`/api/products/` のリソースは `Product` になる。用途の対応は「一覧取得」が `List`、「状態候補取得」が `StatusOptions`、「製品登録」が `Registration`、「詳細取得」が `Detail`、「製品更新」が `Update` である。一覧に無い画面名や用途はエラーにする。アクションの変数名は型と同じ語幹の camelCase で、成功は `Success`、失敗は `Failure` を付ける。型文字列の出典は画面名で、`[Product List] Product List` のようにする。Service のメソッド名は HTTP メソッドと用途を続ける。`getProductList` のようになる。

## 型

| 仕様 | TypeScript |
| --- | --- |
| `string` | `string` |
| `integer` | `number` |
| `number` | `number` |
| `boolean` | `boolean` |
| `date` | `string` |
| `datetime` | `string` |
| 名前付き型 | PascalCase の interface |
| `型[]` | 要素型の配列 |
| `nullable: Yes` | `T \| null` |
| `required: No` | プロパティを省略可能にする |

`object`、`object[]`、未宣言の名前、二重配列は `UNSUPPORTED_TYPE` で停止する。

`state_types` に初期値の項目は無い。初期 state の数値 `0`、文字列 `""`、真偽値 `false`、配列 `[]`、名前付きオブジェクトの必須項目は、TypeScript の型を満たすゼロ値である。11.1 に初期ページ、初期表示件数、初期ソートがあるときは、`pagination.page`、`pagination.pageSize`、`sort.ordering` だけその値にする。

## 生成ファイル

一覧画面「製品一覧」では次を出す。

- `product-list/models/product-list.models.ts`
- `product-list/store/product-list.state.ts`
- `product-list/store/product-list.actions.ts`
- `product-list/store/product-list.reducer.ts`
- `product-list/store/product-list.effects.ts`
- `product-list/store/product-list.selectors.ts`
- `product-list/services/product-list-api.service.ts`
- `product-list/product-list.steps.ts`
- エリアごとのコンポーネント（`.ts` と `.html`）。LIST で `state_path[] .項目` の表示項目があるときは表を出す
- 画面コンポーネント（エリアを順に並べ、初期化アクションがあれば `ngOnInit` で送る）
- `product-list/product-list.module.ts`

エリア種別は `QUERY`、`ACTIONS`、`LIST`、`FORM`、`DETAIL`。同じ種別が複数あるときは、2件目からフォルダ名とクラス名に連番を付ける。エリア ID はファイル名に使わない。

コンポーネントは `standalone: false`。Feature module は `StoreModule.forFeature`、`EffectsModule.forFeature`、`ReactiveFormsModule` を import する。`HttpClient` は Service だけが `inject` する。Feature module の `providers` に `provideHttpClient()` と Service を置く。

## 実行する仕様と転記する仕様

Effects が実行するのは、API ごとの `CALL_API` に対応するアクションである。リクエスト項目はアクションの props で受け取り、Service が `HttpClient` を呼ぶ。成功時、reducer は `response_mappings` の反映先へレスポンス項目を代入する。`SET` と `REPLACE` は、いずれも宣言された項目の代入である。

画面を開くと `initialize` アクションを 1 回送る。Effect は初期化の並びを見て、次だけをその場で dispatch する。

- `CALL_API`。必須パラメータの source がすべて `state_types` にあるとき。任意パラメータで source が state に無いものは省く
- `CALL_EVENT` が参照するイベント操作のうち `CALL_API`。同じ条件

必須パラメータの source が state に無く、初期化の依存を満たせない API は dispatch しない。ID は作らない。初期化の `CALL_API` が `READ_ROUTE` に依存し、ほかの依存が値 `EMPTY` の `input` 初期値だけのとき、source が `route.{名前}` で画面 URL に `:{名前}` があれば、そのパスパラメータを読む。整数として読めないときは API を呼ばない。応答を `input.{項目}` へ入れる指定は、フォームの同名コントロールへ書く。`APPLY_DEFAULTS` 自体は実行しない。フォームの初期値は空文字である。検索の `RESET_PAGE` は 11.1 の初期ページへ戻す。ページ変更、表示件数変更、ソート変更は一覧を取り直す。件数変更とソート変更は、その前に初期ページへ戻す。表示件数の候補は 11.1 の表示件数候補である。

一覧エリアは、source が `{state_path}[].{項目}` で、その `state_path` が state にある表示項目だけを表にする。`CODE:コードID` は codes の表示名へ変換し、未知のコードはその項目の `empty_display` を出す。integer の `id` 列があり、画面 URL が `/` で始まり `:` と `{` を含まないときは、行クリックを `{画面URL}/{id}`、行の編集アイコンを `{画面URL}/{id}/edit` にする。`id` は行の値で、`encodeURIComponent` する。発生条件が「検索結果0件」で画面動作が「空状態を表示」のときは、その一覧へ結果を書く API が成功し、件数が 0 のときだけメッセージを出す。成功前は出さない。

詳細エリアは、source が state のオブジェクト以下の項目である表示を出す。`TEXT` は空文字を `empty_display` にする。`NUMBER` は null のとき `empty_display` にする。

検索ボタンは、ステップが `VALIDATE`、`RESET_PAGE`、`APPLY_QUERY`、`CALL_API` だけのイベントに出す。`VALIDATE` と `APPLY_QUERY` の参照先が `QUERY` のとき、その入力を Reactive Form にする。チェックに失敗したら API は呼ばない。`query.applied` の任意項目は空なら送らず、必須の state 項目は今の state を渡す。`RESET_PAGE` は 11.1 の初期ページをその項目へ書く。

ステップが `NAVIGATE` だけのボタンは `Router.navigateByUrl` で遷移する。`parameters` が `NONE` のときはその URL へ進む。`名前=route.名前` で遷移先の `{名前}` と一致するときは、画面 URL のその値を入れる。整数として読めないときは遷移しない。

`FORM` の入力も Reactive Form にする。保存ボタンは、ステップが `VALIDATE`（参照先 `FORM`）、`CALL_API`、末尾のパラメータ無し `NAVIGATE` のときに出す。チェックに失敗したら API は呼ばない。`input` の必須項目はフォームの値を body に入れる。API が成功したあと、その URL へ遷移する。有効条件に `FORM_VALID` があるボタンは、チェックを満たすまで無効にする。11.2 の二重送信防止が `Yes` の保存は、その通信が成功するか失敗するまでもう一度送らない。有効条件に `NOT_LOADING` があるボタンは、そのボタンが呼ぶ API の通信中は押せない。通信が終わると再び押せる。読み込み中の文言は出さない。二重送信防止が付いた保存は、その防止だけで通信中の再送信を止める。`route.{名前}` は、画面 URL に `:{名前}` があるときボタンがそのパスパラメータを読む。整数として読めないときは API を呼ばない。それ以外で必須 source が state にもフォームにも無い API のボタンは出さない。

`MARK_PRISTINE` は、依存する初期化の `CALL_API` がすべて成功したあと、フォームを未変更に戻す。どれかが失敗したときは戻さない。

次の操作は既知なのでエラーにしない。実行コードは出さず、steps の定数にする。

`APPLY_DEFAULTS`

この一覧に無い操作、HTTP メソッド、パラメータ位置、マッピング、エリア種別はエラーにする。

`query.applied.*`、`input.*`、`route.*` は `state_types` の項目ではない。Effects はそれらを store から読まない。呼び出し側がアクションの props に渡す。

任意の query は `undefined` のとき送信しない。これはリクエストの `required: No` に従う。PATH の `{param}` は同名の PATH パラメータで置き換える。任意の PATH や、URL とパラメータの不一致はエラーである。

失敗アクションは `message: string` を持つ。エラー用の `state_path` が無いので、reducer は失敗で state を変えない。

## Generator が読む JSON

- `source`
- `metadata.screen_id`、`screen_name`、`screen_type`、`url`
- `areas` の `area_id`、`area_name`、`area_type`
- `named_type_catalog`、`named_type_fields`
- `state_types`
- `apis`、`requests`、`responses`、`response_mappings`
- `initialization`、`events`、`event_steps`
- `navigation`、`defaults`、`codes`、`screen_errors`
- `displays` の `area_id`、`label`、`source`、`display_format`、`empty_display`。型検査にも `data_type` を使う
- 型検査のため `inputs`、`route_parameters` の `data_type`

`QUERY` と `FORM` の入力、実行対象のボタン、一覧の表示項目、検索結果 0 件の空状態は画面コードに出す。ダイアログ、書式、空値、戻る遷移、未保存変更、受け入れ条件、非機能、section_status は出さない。

複数画面の URL は `host` で `RouterModule.forRoot` に載せる。各ルートは `pathMatch: "full"` である。`products/new` は `products/:id` より前に置く。ルートコンポーネントは `router-outlet` だけを持つ。Feature module には `RouterModule.forRoot` を足さない。

## 書き込み

- 出力パスに `..`、絶対パス、ドライブ指定があれば拒否する
- 改行は LF、末尾改行は 1 つ
- タイムスタンプは入れない
- 同じ入力から同じバイト列を出す
- 既存ファイルの内容が違うときは `OVERWRITE` で停止し、1 件も書き込まない
- 内容が同じファイルは `UNCHANGED` として残す
- `--dry-run` はディレクトリを作らない

## CLI

```bash
python -m generator.cli plan --model toolchain/models/list-screen-spec.json
python -m generator.cli generate --model toolchain/models/list-screen-spec.json --output generated --dry-run
python -m generator.cli generate --model toolchain/models/list-screen-spec.json --output generated
```

`plan` は相対パス、テンプレート名、依存ファイルを表示する。
