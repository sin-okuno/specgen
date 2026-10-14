// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
export interface ProductSummary {
  id: number;
  name: string;
  status: string;
}

export interface StatusOption {
  label: string;
  value: string;
}

/** 一覧取得 GET /api/products/ */
export interface ProductListRequest {
  /** source: query.applied.productName; location: QUERY */
  name?: string;
  /** source: query.applied.status; location: QUERY */
  status?: string;
  /** source: pagination.page; location: QUERY */
  page: number;
  /** source: pagination.pageSize; location: QUERY */
  page_size: number;
  /** source: sort.ordering; location: QUERY */
  ordering: string;
}

/** 一覧取得 GET /api/products/ */
export interface ProductListResponse {
  count: number;
  results: ProductSummary[];
}

/** 状態候補取得 GET /api/products/options/ */
export interface ProductStatusOptionsResponse {
  statuses: StatusOption[];
}

export const productListCodes = {
  "CODE-001": {
    new: "新規",
    closed: "完了",
  },
} as const;

export const productListScreenErrors = [
  {
    errorId: "ERR-001",
    condition: "検索結果0件",
    message: "データがありません",
    behavior: "空状態を表示",
  },
] as const;
