// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品登録
// source: create-screen-spec.md
export interface StatusOption {
  label: string;
  value: string;
}

/** 製品登録 POST /api/products/ */
export interface ProductRegistrationRequest {
  /** source: input.productName; location: BODY */
  name: string;
  /** source: input.status; location: BODY */
  status: string;
}

/** 製品登録 POST /api/products/ */
export interface ProductRegistrationResponse {
  id: number;
  name: string;
  status: string;
}

/** 状態候補取得 GET /api/products/options/ */
export interface ProductStatusOptionsResponse {
  statuses: StatusOption[];
}

export const productRegistrationCodes = {
  "CODE-001": {
    new: "新規",
    closed: "完了",
  },
} as const;

