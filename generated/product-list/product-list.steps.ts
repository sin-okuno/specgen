// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
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

export const productListScreenType = "LIST";

export const productListScreenUrl = "/products";

export const productListInitialization = [
  {
    initId: "INIT-001",
    operation: "APPLY_DEFAULTS",
    description: "検索条件初期化",
    condition: "ALWAYS",
    dependsOn: "NONE",
    reference: "DEFAULTS",
  },
  {
    initId: "INIT-002",
    operation: "CALL_API",
    description: "候補取得",
    condition: "ALWAYS",
    dependsOn: "INIT-001",
    reference: "API-002",
  },
  {
    initId: "INIT-003",
    operation: "CALL_EVENT",
    description: "初期検索",
    condition: "ALWAYS",
    dependsOn: "INIT-001",
    reference: "EVT-001",
  },
] as const;

export const productListEvents = [
  {
    eventId: "EVT-001",
    eventName: "検索",
    trigger: "ON_INIT,ON_CLICK",
    origin: "INIT-003,searchButton",
    description: "製品検索",
  },
  {
    eventId: "EVT-002",
    eventName: "新規登録",
    trigger: "ON_CLICK",
    origin: "createButton",
    description: "登録画面遷移",
  },
  {
    eventId: "EVT-003",
    eventName: "ページ変更",
    trigger: "ON_CHANGE",
    origin: "pagination.page",
    description: "ページ移動",
  },
  {
    eventId: "EVT-004",
    eventName: "表示件数変更",
    trigger: "ON_CHANGE",
    origin: "pagination.pageSize",
    description: "表示件数変更",
  },
  {
    eventId: "EVT-005",
    eventName: "ソート変更",
    trigger: "ON_CHANGE",
    origin: "sort.ordering",
    description: "ソート変更",
  },
] as const;

export const productListEventSteps = [
  {
    eventId: "EVT-001",
    step: "1",
    operation: "VALIDATE",
    description: "検索条件チェック",
    condition: "ALWAYS",
    reference: "QUERY",
    onSuccess: "NEXT",
    onFailure: "STOP",
  },
  {
    eventId: "EVT-001",
    step: "2",
    operation: "RESET_PAGE",
    description: "検索開始時に先頭ページへ",
    condition: "ALWAYS",
    reference: "pagination.page",
    onSuccess: "NEXT",
    onFailure: "STOP",
  },
  {
    eventId: "EVT-001",
    step: "3",
    operation: "APPLY_QUERY",
    description: "入力中の検索条件を適用",
    condition: "ALWAYS",
    reference: "QUERY",
    onSuccess: "NEXT",
    onFailure: "STOP",
  },
  {
    eventId: "EVT-001",
    step: "4",
    operation: "CALL_API",
    description: "一覧取得",
    condition: "ALWAYS",
    reference: "API-001",
    onSuccess: "END",
    onFailure: "COMMON_ERROR",
  },
  {
    eventId: "EVT-002",
    step: "1",
    operation: "NAVIGATE",
    description: "登録画面へ遷移",
    condition: "ALWAYS",
    reference: "NAV-001",
    onSuccess: "END",
    onFailure: "STOP",
  },
  {
    eventId: "EVT-003",
    step: "1",
    operation: "CALL_API",
    description: "指定ページ取得",
    condition: "ALWAYS",
    reference: "API-001",
    onSuccess: "END",
    onFailure: "COMMON_ERROR",
  },
  {
    eventId: "EVT-004",
    step: "1",
    operation: "RESET_PAGE",
    description: "先頭ページに戻す",
    condition: "ALWAYS",
    reference: "pagination.page",
    onSuccess: "NEXT",
    onFailure: "STOP",
  },
  {
    eventId: "EVT-004",
    step: "2",
    operation: "CALL_API",
    description: "表示件数変更後の取得",
    condition: "ALWAYS",
    reference: "API-001",
    onSuccess: "END",
    onFailure: "COMMON_ERROR",
  },
  {
    eventId: "EVT-005",
    step: "1",
    operation: "RESET_PAGE",
    description: "先頭ページに戻す",
    condition: "ALWAYS",
    reference: "pagination.page",
    onSuccess: "NEXT",
    onFailure: "STOP",
  },
  {
    eventId: "EVT-005",
    step: "2",
    operation: "CALL_API",
    description: "ソート変更後の取得",
    condition: "ALWAYS",
    reference: "API-001",
    onSuccess: "END",
    onFailure: "COMMON_ERROR",
  },
] as const;

export const productListNavigation = [
  {
    navId: "NAV-001",
    eventId: "EVT-002",
    target: "/products/new",
    condition: "ALWAYS",
    parameters: "NONE",
  },
] as const;

export const productListDefaults = [
  {
    destination: "input.productName",
    value: "EMPTY",
  },
  {
    destination: "input.status",
    value: "EMPTY",
  },
] as const;
