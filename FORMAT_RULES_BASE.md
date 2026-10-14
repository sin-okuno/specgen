# 共通Markdown画面仕様書 v1.5 — 記法・整合性規約

**状態：正式版候補（検証範囲限定）**  
**対象：LIST / CREATE / EDIT / DETAIL**

## 1. 基本方針

- 14章と章・節見出しを共通化する。非該当節は `対象外` とする。
- 構造化表を正とし、自由記述は生成ロジックの根拠にしない。
- Parserは構文を読み、Validatorは参照・型・実行フローを検証する。エラー時は生成しない。
- API側で認証・認可を行い、HTTP 403はAngular共通エラー処理に委ねる。画面独自の表示制御だけ9.2に記す。

## 2. 固定参照名前空間

| 参照形式 | 意味 | 読書き |
|---|---|---|
| `input.<itemId>` | 3.1の入力項目 | R/W |
| `query.applied.<itemId>` | 検索実行時に確定した条件（LISTのみ） | R |
| `route.<param>` | 4.3のURLパラメータ | R |
| `data.<path>` | 画面内の取得済みデータ | R/W |
| `list.items` | LIST結果配列 | R/W |
| `pagination.page` | 1始まりページ番号 | R/W |
| `pagination.pageSize` | 1ページ件数 | R/W |
| `pagination.total` | 総件数 | R/W |
| `sort.ordering` | APIソート文字列 | R/W |
| `options.<OPT-ID>` | 選択肢配列 | R/W |
| `const.<name>` | 共通定数定義への参照 | R |

`data` のスキーマは6.4の反映先および3.2の参照から構成し、同一パスで型が食い違えばエラー。`const` を使う場合は共通定数定義を別途必須とする。配列は `list.items[].name` のように `[]` を使う。

## 3. 初期表示の確定規則

- 4.1は **DAG（有向非巡回グラフ）**。依存先IDが存在しない・循環する場合はエラー。
- `APPLY_DEFAULTS` は4.2の全行を一度だけ適用する。4.1の参照先は `DEFAULTS` 固定。4.2が対象外なら使わない。
- `READ_ROUTE` の参照先は4.3に定義した `route.<param>` と一致させる。
- `CALL_API` は6.1のAPI ID、`CALL_EVENT` は5.1のイベントIDを参照する。
- `CALL_EVENT` で呼ぶイベントは `ON_INIT` を含み、イベント側から別の自動ON_INIT呼出しを生成しない（二重実行防止）。
- `MARK_PRISTINE` はフォーム初期化と取得値反映が完了した後で実行する。参照先は `FORM`。
- `CALL_API` の完了は、レスポンスを受信し6.4の該当マッピングを**すべて反映し終えた時点**。失敗した処理に依存する後続処理は起動しない。
- 依存のない処理は並行実行できる。ただし同じ反映先に並行書込みがある場合は競合エラーとする。
- API失敗時は共通エラー処理を呼び、依存する初期処理を中止する。

## 4. イベント実行規則

- 5.2のステップはイベントIDごとに1から連番。各ステップは `NEXT`、`END`、`STOP`、`COMMON_ERROR`、`STEP:n` のいずれかへ進む。
- `NEXT` は次ステップがある場合のみ有効。最後のステップの成功は `END` とする。
- `STEP:n` は存在する同イベント内のステップを参照し、後方参照のみ許可する（ループは禁止）。
- `VALIDATE` の参照先は `FORM` または `QUERY`。不正時は `STOP` とする。
- `RESET_PAGE` の参照先は `pagination.page` 固定。`APPLY_QUERY` は参照先 `QUERY` 固定で `input.*` の検索条件を `query.applied.*` にスナップショットする。初回検索も同様。
- LISTの検索API Requestは常に `query.applied.<itemId>` を参照する。ページング・ソートでは `APPLY_QUERY` を実行しない。APIが失敗してもスナップショットは保持し、再試行時に同じ条件を利用する。
- `CONFIRM` は5.3のダイアログIDを参照する。5.3の `OK時` と `キャンセル時` はそれぞれ `NEXT` / `STOP` / `STEP:n` / `END` のいずれかで、5.2の `成功時` / `失敗時` と一致させる。保存前確認=Yesなら保存API前にCONFIRMが必須。NoならCONFIRMを設けない。
- `NAVIGATE` は8.1のNAV IDを参照する。遷移先の `{id}` は8.1のパラメータから解決する。
- `SET_VALUE` を使用する場合、参照先は `代入先=設定元` の**1代入のみ**。複数代入はステップを分割する。値は `EMPTY`、`NULL`、`TRUE`、`FALSE`、型付きリテラルまたは上記名前空間の参照とする。

## 5. API規則

- 6.1にAPIを列挙。6.2のPATH/QUERY/BODY/HEADER、6.3のResponseフィールド、6.4の反映先をAPI IDで結ぶ。
- `{id}` などEndpoint内のプレースホルダーは、同じ名前のPATH送信項目が6.2に**ちょうど1つ**必要。
- 6.3の配列は親 `results: product[]` とし、`product` の内部フィールドを6.6で定義する。
- 6.4の `Response項目` は6.3に存在し、`SET` はスカラー/単一オブジェクト、`REPLACE` は配列または全体置換、`APPEND` は配列末尾追加に使用する。
- `REPLACE results -> list.items` は配列要素の形を保って格納する。3.2の `list.items[].field` は6.3の `results[].field` で検証する。
- `input.*` にResponseを反映する際は値更新を行う。EDITの初期取得後は `MARK_PRISTINE` で変更検知をリセットする。
- 6.4に反映先がないResponseフィールドは無視してよいが、3.2から参照されるパスは必ず反映されていなければならない。

## 6. URL・画面遷移

- 画面URLの `:id` は4.3の `id` と一致させる。
- 8.1の遷移先は `/products/{id}` のように `{param}` で記載する。`:id` は画面基本情報のルート定義URLでのみ許可する。パラメータ列は `id=route.id` などの `名前=参照` とする。`NONE` は引数なし。
- 戻る処理は遷移先が明確な場合のみ自動生成する。`RESTORE` は検索条件、ページ、表示件数、ソート条件を復元する。
- `未保存変更確認=Yes` の場合、8.3の `確認ダイアログ` は5.3に定義済みであること。`変更検知` は `IS_DIRTY`、`確認対象` は `画面離脱時` とする。Angularの画面離脱ガードが、画面遷移・ブラウザ履歴操作を含む離脱時に確認を実施する。ガード用ダイアログは5.2のCONFIRMステップとは別扱いとし、二重表示しない。ブラウザタブ終了・再読み込みはブラウザ標準確認に従う。Noの場合は8.3を対象外にする。

## 7. エラー条件（主要）

| コード | 条件 | 判定 |
|---|---|---|
| MD001 | 14章不足・順序違反・表ヘッダー不一致 | ERROR |
| REF001 | 未定義のAREA/EVT/API/NAV/OPT参照 | ERROR |
| REF002 | 名前空間参照先またはResponse項目が未定義 | ERROR |
| FLOW001 | INITの依存ID不正・循環・並行書込み競合 | ERROR |
| FLOW002 | ON_INITがCALL_EVENTと整合しない | ERROR |
| FLOW003 | イベントステップ遷移先が存在しない・ループ | ERROR |
| API001 | EndpointプレースホルダーとPATHパラメータ不一致 | ERROR |
| API002 | Responseと反映先の型不一致 | ERROR |
| FORM001 | 必須のフォーム初期化/取得値反映/変更検知が不整合 | ERROR |
| NAV001 | 遷移パラメータが解決不能 | ERROR |
| UNS001 | 自由記述のみで生成が必要な振る舞いを指定 | ERROR |

## 8. 仕様の扱い

本ファイルは**v1.5レビュー用候補**。4つのサンプルの静的整合性チェック後に凍結する。実際のParser実装による検証・Angularビルド検証は未実施。

## 9. v1.5で追加した機械検証ルール

- LISTの検索APIは `query.applied.*` のみを検索条件の設定元に使い、検索イベントに `APPLY_QUERY` がちょうど1回含まれる。ページング・ソートのイベントには含まれない。
- `query.applied.<itemId>` のitemIdは3.1で宣言済みでなければならない。
- 5.2のCONFIRM参照は5.3のダイアログIDに存在し、分岐先が一致する。
- 8.1の遷移先では `:id` を使用しない。
- 11.2の保存前確認と11.3の未保存変更確認は `Yes/No` を明示し、Yesなら必要な構造化定義を備える。
- 4.1の表の行順は実行順ではない。依存関係DAGのみを実行順の根拠とする。

## 10. 残る検証課題

`data.*` の状態スキーマ、Responseのネストした型照合、条件式の完全な型検証、実行時の排他・状態復元、Angularコード生成とビルドは未検証。正式凍結はこれらのうち仕様フォーマットに影響する事項を整理した後に判断する。

## 11. 名前付き複合型定義（6.6）— 改訂

- `object` および `object[]` は6.2/6.3のデータ型として禁止する。`component`、`component[]` など**定義済みの名前付き型**を使う。
- プリミティブ型は `string`、`integer`、`number`、`boolean`、`date`、`datetime`。配列は `型名[]` で表す。
- 6.6.1型一覧と6.6.2型フィールド定義を使用する。型名は英字始まりの英数字・アンダースコアで、大文字小文字を区別する。組込型名と重複不可。
- すべての複合型は6.6.1に宣言し、6.6.2に少なくとも1フィールドを定義する。フィールド名は型内で一意。
- 複合型フィールドのデータ型にはプリミティブ型、定義済み複合型、またはその配列を指定できる。循環参照は禁止する（再帰データは将来検討）。
- Request/Responseに現れる複合型は必ず6.6で解決可能とする。フィールドの必須・NULL許可は型定義に従い、API単位で異なる場合は別名の型（例：`componentCreate`、`componentDetail`）を宣言する。
- 6.2の複合型Requestは設定元を `input.components` のように型が一致する値への参照とし、子フィールドを6.2に再列挙しない。配列も同様。個別フィールドから組み立てる場合は画面状態に構築済みの名前付き型を宣言する必要がある（本版では任意の `STRUCT` 組立ては対象外）。
- 6.3の複合型Responseも子パスを再列挙せず、6.6の定義を参照する。`components[].name` などの参照先型は6.6をたどって検証する。
- 6.4で `components` を `data.product.components` に反映する場合は、反映先も `component[]` でなければならない。型が異なる場合は明示的な変換定義が必要（本版では自動変換禁止）。
- 6.6は14章構成の第6章内に追加する。型一覧・型フィールド定義が不要な画面は `対象外` とする。複数画面間の型共有は将来の共通型カタログで検討し、現段階では各画面仕様書に必要な型を明示する。

### 11.1 6.2 API Request例

| API ID | パラメータ | データ型 | 必須 | 設定元 | 送信形式 |
|---|---|---|---|---|---|
| API-001 | name | string | Yes | input.productName | BODY |
| API-001 | components | component[] | Yes | input.components | BODY |

### 11.2 6.3 API Response例

| API ID | フィールド | データ型 | 必須 | NULL許可 |
|---|---|---|---|---|
| API-001 | id | integer | Yes | No |
| API-001 | name | string | Yes | No |
| API-001 | manufacturer | manufacturer | Yes | No |
| API-001 | components | component[] | Yes | No |

### 11.3 6.6.1 型一覧

| 型名 | 説明 |
|---|---|
| manufacturer | メーカー |
| component | 部品 |

### 11.4 6.6.2 型フィールド定義

| 型名 | フィールド | データ型 | 必須 | NULL許可 |
|---|---|---|---|---|
| manufacturer | id | integer | Yes | No |
| manufacturer | name | string | Yes | No |
| component | id | integer | Yes | No |
| component | name | string | Yes | No |
| component | quantity | integer | Yes | No |

### 11.5 Validator追加エラー

| コード | 条件 | 判定 |
|---|---|---|
| TYPE001 | 未定義の複合型を参照 | ERROR |
| TYPE002 | 複合型にフィールド定義がない | ERROR |
| TYPE003 | 型名または型内フィールド名が重複 | ERROR |
| TYPE004 | 複合型の循環参照 | ERROR |
| TYPE005 | Request設定元と名前付き型・配列型が不一致 | ERROR |
| TYPE006 | Response反映先と名前付き型・配列型が不一致 | ERROR |
| TYPE007 | API定義で禁止型 `object` / `object[]` を使用 | ERROR |
| TYPE008 | 型定義フィールドの必須・NULL許可が不正 | ERROR |

**移行注意**：旧v1.5サンプル中の `object` / `object[]` を `product` / `product[]` 等に置き換える場合は、対応する6.6定義を追加する。旧Validator v0.3はこの方式に未対応であり、上記のエラー検査は実装済みとはみなさない。
