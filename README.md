# 共通Markdown画面仕様書 v1.5 と Screen Generator

対象は Angular 22 の LIST / CREATE / EDIT / DETAIL です。仕様書の正本は Markdown、Generator の入力は検証済みの Screen Model JSON です。コマンドはリポジトリ直下で実行します。

## 正本と優先順位

1. `SPECIFICATION_V1.5.md`: 固定版の適用範囲と記法の優先順位。
2. `FORMAT_RULES_BASE.md`: 元の14章共通ルール。ただし旧版の「未実装」「候補」「未検証」などの記述は本固定版の検証結果に読み替える。
3. `CONDITION_RULES.md`, `STATE_NAV_RULES.md`: 後続の追加ルール（競合する場合は追加ルール優先）。
4. `examples/*.md`: 4画面の実例。

`toolchain/` の `examples/` と `models/` はテストを単独で実行できるよう同梱した複製です。正本の例はトップレベルの `examples/` です。Generator は Parser と Validator を変更しません。

## 準備

Python 3.12 以上と、画面を起動する場合は Node.js が必要です。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "jinja2>=3.1.4" "jsonschema>=4.23.0" "pytest>=8.3" "ruff>=0.8"
```

Python の依存は `pyproject.toml` にも書いてあります。以降の `python` は `.\.venv\Scripts\python.exe` を指します。

## 仕様書を検証する

Markdown から JSON を作り、schema とモデル検証を通します。4画面をまとめて渡すと、遷移先が揃っていることを確認できます。

```powershell
python toolchain\pipeline.py examples --output-dir toolchain\models --report toolchain\validation-report.json
python -m unittest discover -s toolchain\tests -v
```

成功した画面だけが `toolchain\models\` に JSON として残ります。一覧だけの JSON を既存の `toolchain\validate_json.py` に渡すと、遷移先 `/products/new` が同一セットに無いため失敗します。

## 画面を生成する

入力は検証済み JSON です。1回の `generate` は画面1つです。付属の4画面は次の順で出します。

```powershell
python -m generator.cli plan --model toolchain\models\list-screen-spec.json
python -m generator.cli generate --model toolchain\models\list-screen-spec.json --output generated --dry-run
python -m generator.cli generate --model toolchain\models\list-screen-spec.json --output generated
python -m generator.cli generate --model toolchain\models\create-screen-spec.json --output generated
python -m generator.cli generate --model toolchain\models\edit-screen-spec.json --output generated
python -m generator.cli generate --model toolchain\models\detail-screen-spec.json --output generated
```

`plan` は書く予定のファイルを表示します。`--dry-run` はファイルを作りません。同じ内容のファイルは `UNCHANGED` です。既存ファイルと内容が違うときは `OVERWRITE` で停止し、1件も書きません。出し直すときは、対象のディレクトリを消してから `generate` します。

```powershell
Remove-Item -Recurse -Force generated\product-list
python -m generator.cli generate --model toolchain\models\list-screen-spec.json --output generated
```

設計は `GENERATOR_DESIGN.md`、実行結果の記録は `GENERATION_REPORT.md` です。

## 4画面をURLでつなぐ

各画面の `navigateByUrl` を載せるルートを `generated\app\` に作ります。`generate` で4画面を出したあとで実行します。

```powershell
python -m generator.cli host --model toolchain\models\list-screen-spec.json --model toolchain\models\create-screen-spec.json --model toolchain\models\edit-screen-spec.json --model toolchain\models\detail-screen-spec.json --output generated
```

`host` も、既存ファイルと内容が違うときは `OVERWRITE` で停止します。出し直すときは `generated\app` を消してから実行します。

## 画面を開く

```powershell
npm install
npm start
```

`npm start` は `AppModule` を `http://127.0.0.1:4200/` で起動します。

| URL | 画面 |
| --- | --- |
| `/products` | 製品一覧 |
| `/products/new` | 製品登録 |
| `/products/1` | 製品詳細。`1` は整数の id |
| `/products/1/edit` | 製品更新 |

Service は仕様のパスをそのまま呼びます。API のベース URL は付けていません。

## テスト

```powershell
python -m pytest tests/generator -q
python -m ruff check generator tests
```

## 制約

仕様書フォーマットの検証は、API の実行結果や条件分岐の完全な証明にはなりません。生成した画面は、読み込み中の文言、権限の画面、通信失敗の表示を持っていません。
