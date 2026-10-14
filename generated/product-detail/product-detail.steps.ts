// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品詳細
// source: detail-screen-spec.md
// 画面を開くと、初期化の CALL_API と、CALL_EVENT が参照する操作のうち CALL_API だけを実行する。
// その CALL_API が READ_ROUTE に依存し、ほかの依存が空の入力初期値だけのときは、画面 URL のパスパラメータを読んで渡す。
// 応答の input への代入は、フォームの同名コントロールへ入れる。
// 検索ボタンは VALIDATE、APPLY_QUERY、RESET_PAGE、CALL_API を実行する。
// ページ、表示件数、ソートの変更でも一覧を取り直す。件数とソートの変更はページを初期ページに戻す。
// 一覧の取得結果が 0 件のときは、その取得が終わったあとだけ空状態のメッセージを出す。
// パラメータが NONE の NAVIGATE ボタンは、その URL へ遷移する。
// パラメータが route の同名項目で、遷移先のプレースホルダと一致するときは、画面 URL の値を入れて遷移する。
// 保存は VALIDATE と CALL_API を実行し、API 成功後にパラメータ無しの遷移を行う。
// 登録の二重送信防止が Yes の保存は、その通信が終わるまでもう一度送らない。
// 有効条件に NOT_LOADING があるボタンは、そのボタンの API 通信中は押せない。通信が終わると再び押せる。
// APPLY_DEFAULTS は定数のまま。フォームの初期値は空である。
// MARK_PRISTINE は、依存する初期化の API がすべて成功したあとフォームを未変更に戻す。失敗したときは戻さない。

export const productDetailScreenType = "DETAIL";

export const productDetailScreenUrl = "/products/:id";

export const productDetailInitialization = [
  {
    initId: "INIT-001",
    operation: "READ_ROUTE",
    description: "ID取得",
    condition: "ALWAYS",
    dependsOn: "NONE",
    reference: "route.id",
  },
  {
    initId: "INIT-002",
    operation: "CALL_API",
    description: "製品取得",
    condition: "ALWAYS",
    dependsOn: "INIT-001",
    reference: "API-001",
  },
] as const;

export const productDetailEvents = [
  {
    eventId: "EVT-001",
    eventName: "編集画面へ遷移",
    trigger: "ON_CLICK",
    origin: "editButton",
    description: "編集画面へ遷移処理",
  },
  {
    eventId: "EVT-002",
    eventName: "キャンセル・戻る",
    trigger: "ON_CLICK",
    origin: "backButton",
    description: "一覧へ遷移",
  },
] as const;

export const productDetailEventSteps = [
  {
    eventId: "EVT-001",
    step: "1",
    operation: "NAVIGATE",
    description: "編集画面へ遷移",
    condition: "ALWAYS",
    reference: "NAV-001",
    onSuccess: "END",
    onFailure: "STOP",
  },
  {
    eventId: "EVT-002",
    step: "1",
    operation: "NAVIGATE",
    description: "一覧へ戻る",
    condition: "ALWAYS",
    reference: "NAV-002",
    onSuccess: "END",
    onFailure: "STOP",
  },
] as const;

export const productDetailNavigation = [
  {
    navId: "NAV-001",
    eventId: "EVT-001",
    target: "/products/{id}/edit",
    condition: "ALWAYS",
    parameters: "id=route.id",
  },
  {
    navId: "NAV-002",
    eventId: "EVT-002",
    target: "/products",
    condition: "ALWAYS",
    parameters: "NONE",
  },
] as const;

export const productDetailDefaults = [
] as const;
