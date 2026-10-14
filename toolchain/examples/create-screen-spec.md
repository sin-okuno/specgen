# 画面仕様書：製品登録

**仕様書バージョン：** 1.5  
**画面種別：** CREATE

## 1. 画面基本情報

| 項目 | 内容 |
|---|---|
| 画面ID | SCR-002 |
| 画面名 | 製品登録 |
| 画面種別 | CREATE |
| URL | /products/new |
| 画面概要 | 製品の製品登録を行う |
| 対象ユーザー | 認証済みユーザー |
| 関連画面 | SCR-001,SCR-002,SCR-003,SCR-004 |
| 共通認可仕様 | API側で認可判定 |
| 共通エラー仕様 | HTTP 403は共通権限エラー表示 |

## 2. 画面構成

### 2.1 画面構成要素

| 領域ID | 領域名 | 領域種別 | 概要 | 表示条件 |
|---|---|---|---|---|
| AREA-001 | 製品情報 | FORM | 製品情報の入力・表示 | ALWAYS |
| AREA-002 | 操作 | ACTIONS | 画面操作 | ALWAYS |

### 2.2 画面レイアウト

| 表示順 | 領域ID | 配置 |
|---|---|---|
| 1 | AREA-001 | TOP |
| 2 | AREA-002 | CENTER |

## 3. 画面項目定義

### 3.1 入力項目

| 項目ID | 領域ID | 項目名 | UI種別 | データ型 | 必須 | 初期値 | 入力制約 | チェックタイミング | エラー文言 |
|---|---|---|---|---|---|---|---|---|---|
| productName | AREA-001 | 製品名 | TEXT | string | Yes | EMPTY | required;maxLength:100 | ON_EXECUTE | 製品名を1〜100文字で入力してください |
| status | AREA-001 | 状態 | SELECT | string | Yes | EMPTY | required;options:OPT-001 | ON_EXECUTE | 状態を選択してください |

### 3.2 表示項目

対象外

### 3.3 操作項目

| 項目ID | 領域ID | 項目名 | UI種別 | イベントID | 表示条件 | 活性条件 |
|---|---|---|---|---|---|---|
| saveButton | AREA-002 | 保存 | BUTTON | EVT-001 | ALWAYS | FORM_VALID && NOT_LOADING |
| cancelButton | AREA-002 | キャンセル | BUTTON | EVT-002 | ALWAYS | ALWAYS |

### 3.4 表示・活性制御

対象外

### 3.5 相関チェック

対象外

### 3.6 選択候補

| 候補ID | 取得方法 | 取得元 | 表示値 | 内部値 |
|---|---|---|---|---|
| OPT-001 | API | API-002.statuses | label | value |

## 4. 初期表示仕様

### 4.1 初期表示処理

| 処理ID | 処理種別 | 処理内容 | 実行条件 | 依存処理 | 参照先 |
|---|---|---|---|---|---|
| INIT-001 | APPLY_DEFAULTS | フォーム初期化 | ALWAYS | NONE | DEFAULTS |
| INIT-002 | CALL_API | 候補取得 | ALWAYS | INIT-001 | API-002 |

### 4.2 初期値定義

| 設定先 | 設定値 |
|---|---|
| input.productName | EMPTY |
| input.status | EMPTY |

### 4.3 URLパラメータ

対象外

## 5. イベント・操作仕様

### 5.1 イベント一覧

| イベントID | イベント名 | 起動条件 | 発生元 | 処理概要 |
|---|---|---|---|---|
| EVT-001 | 登録 | ON_CLICK | saveButton | 登録処理 |
| EVT-002 | キャンセル・戻る | ON_CLICK | cancelButton | 一覧へ遷移 |

### 5.2 イベント処理ステップ

| イベントID | ステップ | 処理種別 | 処理内容 | 実行条件 | 参照先 | 成功時 | 失敗時 |
|---|---|---|---|---|---|---|---|
| EVT-001 | 1 | VALIDATE | 入力チェック | ALWAYS | FORM | NEXT | STOP |
| EVT-001 | 2 | CALL_API | 登録API呼び出し | ALWAYS | API-001 | NEXT | COMMON_ERROR |
| EVT-001 | 3 | NAVIGATE | 一覧へ遷移 | ALWAYS | NAV-001 | END | STOP |
| EVT-002 | 1 | NAVIGATE | 一覧へ戻る | ALWAYS | NAV-002 | END | STOP |

### 5.3 確認ダイアログ

対象外

## 6. API連携仕様

### 6.1 API一覧

| API ID | 用途 | Method | Endpoint |
|---|---|---|---|
| API-001 | 製品登録 | POST | /api/products/ |
| API-002 | 状態候補取得 | GET | /api/products/options/ |

### 6.2 API Request定義

| API ID | パラメータ | データ型 | 必須 | 設定元 | 送信形式 |
|---|---|---|---|---|---|
| API-001 | name | string | Yes | input.productName | BODY |
| API-001 | status | string | Yes | input.status | BODY |

### 6.3 API Response定義

| API ID | フィールド | データ型 | 必須 | NULL許可 |
|---|---|---|---|---|
| API-001 | id | integer | Yes | No |
| API-001 | name | string | Yes | No |
| API-001 | status | string | Yes | No |
| API-002 | statuses | statusOption[] | Yes | No |

### 6.4 API Response反映定義

| API ID | Response項目 | 反映先 | 反映方式 |
|---|---|---|---|
| API-001 | id | data.product.id | SET |
| API-002 | statuses | options.OPT-001 | REPLACE |

### 6.5 API共通ルール

| 項目 | 内容 |
|---|---|
| 認証・認可 | API側で実施 |
| HTTP 403 | Angular共通権限エラー表示 |
| 未指定の任意パラメータ | 送信しない |

### 6.6 データ型定義

#### 6.6.1 型一覧

| 型名 | 説明 |
|---|---|
| statusOption | 状態選択候補 |

#### 6.6.2 型フィールド定義

| 型名 | フィールド | データ型 | 必須 | NULL許可 |
|---|---|---|---|---|
| statusOption | label | string | Yes | No |
| statusOption | value | string | Yes | No |

### 6.7 画面状態型定義

| 状態パス | データ型 | NULL許可 |
|---|---|---|
| data.product.id | integer | No |
| options.OPT-001 | statusOption[] | No |

## 7. データ表示・変換仕様

### 7.1 コード変換

| コード定義ID | コード | 表示値 |
|---|---|---|
| CODE-001 | new | 新規 |
| CODE-001 | closed | 完了 |

### 7.2 表示形式

| 表示形式 | 内容 |
|---|---|
| TEXT | 文字列 |
| NUMBER | 数値 |
| CODE:CODE-001 | コード変換 |

### 7.3 空値の扱い

| 値 | 表示 |
|---|---|
| null | - |
| 空文字 | 空欄 |

## 8. 画面遷移仕様

### 8.1 遷移一覧

| 遷移ID | 発生イベント | 遷移先 | 遷移条件 | パラメータ |
|---|---|---|---|---|
| NAV-001 | EVT-001 | /products | ALWAYS | NONE |
| NAV-002 | EVT-002 | /products | ALWAYS | NONE |

### 8.2 戻り先

| 発生イベント | 戻り先 | 状態復元 |
|---|---|---|
| EVT-002 | /products | RESTORE |

### 8.3 未保存変更時の遷移

対象外

## 9. 権限制御

### 9.1 共通認可方針

API側で認証・認可を判定し、HTTP 403はAngular共通エラー処理で表示する。

### 9.2 画面固有の権限制御

対象外

## 10. エラーハンドリング

### 10.1 共通エラー処理

HTTP 401/403/500はフロントエンド共通エラー処理仕様に準拠する。

### 10.2 画面固有のエラー処理

対象外

## 11. 画面固有仕様

### 11.1 LIST仕様

対象外

### 11.2 CREATE仕様

| 項目 | 内容 |
|---|---|
| 保存API | API-001 |
| 保存イベント | EVT-001 |
| 保存前確認 | No |
| 保存成功時遷移 | NAV-001 |
| 保存後フォーム初期化 | No |
| 二重送信防止 | Yes |

### 11.3 EDIT仕様

対象外

### 11.4 DETAIL仕様

対象外

## 12. 非機能要件

| 項目 | 要件 |
|---|---|
| Loading | API処理中に表示 |
| 二重操作防止 | 同一処理の重複実行を抑止 |
| セキュリティ | API側で認証・認可を実施 |
| 対応ブラウザ | Chrome、Edge |

## 13. 受入条件

| 受入ID | 対象 | 前提条件 | 操作 | 期待結果 |
|---|---|---|---|---|
| AC-001 | 初期表示 | API正常 | 画面を開く | 初期表示処理が実行される |
| AC-002 | 認可エラー | APIが403を返す | API呼び出し | 共通権限エラーが表示される |

## 14. 補足・未決事項

対象外

---

## 変更履歴

| 版数 | 更新日 | 変更内容 |
|---|---|---|
| 1.3 | 2026-10-11 | 4画面共通仕様の記入例 |

