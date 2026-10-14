# 条件式・イベント経路ルール v0.6（追加仕様）

`4.1 初期表示` と `5.2 イベント処理ステップ` の `条件` は、以下の機械解析可能な記法に限定します。

| 記法 | 意味 | 例 |
|---|---|---|
| `ALWAYS` | 常に実行 | `ALWAYS` |
| `IS_SET(path)` | 値が設定済み | `IS_SET(route.id)` |
| `IS_EMPTY(path)` | 値が空 | `IS_EMPTY(input.productName)` |
| `EQ(path,value)` | 値が等しい | `EQ(pagination.page,1)` |
| `NE(path,value)` | 値が異なる | `NE(input.status,"DRAFT")` |

- path は宣言済みの `input.*`、`query.applied.*`、`route.*`、`6.7 画面状態型` のパスに限る。
- 比較値は JSON の真偽値、数値、null、二重引用符付き文字列に限る。
- `EQ/NE` の型一致を確認する。`null` の可否検証は未実装。
- JavaScript/Pythonなどの任意式は実行・推測せず `COND001` で拒否する。
- イベント分岐は `NEXT`、`STEP:n`、`END`、`STOP`、`COMMON_ERROR` のみを認識する。
- `FLOW102` で到達不能ステップを、`FLOW103` で終了不能な経路を検出する。
- `FLOW103` は終了へ到達可能かの検査であり、全実行経路の停止を証明しない。

## 未実装（正式版確定前の課題）
- 条件の真偽による分岐の実行可能性・排他性、条件付きINITの実行順序
- 全経路の業務上の正当性、NULLと空値の意味的区別、条件式のAND/OR
- 画面間パラメータの型一致
