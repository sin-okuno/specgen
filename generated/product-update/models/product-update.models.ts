// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品更新
// source: edit-screen-spec.md
export interface StatusOption {
  label: string;
  value: string;
}

/** 詳細取得 GET /api/products/{id}/ */
export interface ProductDetailRequest {
  /** source: route.id; location: PATH */
  id: number;
}

/** 詳細取得 GET /api/products/{id}/ */
export interface ProductDetailResponse {
  id: number;
  name: string;
  status: string;
}

/** 状態候補取得 GET /api/products/options/ */
export interface ProductStatusOptionsResponse {
  statuses: StatusOption[];
}

/** 製品更新 PATCH /api/products/{id}/ */
export interface ProductUpdateRequest {
  /** source: route.id; location: PATH */
  id: number;
  /** source: input.productName; location: BODY */
  name: string;
  /** source: input.status; location: BODY */
  status: string;
}

/** 製品更新 PATCH /api/products/{id}/ */
export interface ProductUpdateResponse {
  id: number;
  name: string;
  status: string;
}

export const productUpdateCodes = {
  "CODE-001": {
    new: "新規",
    closed: "完了",
  },
} as const;

