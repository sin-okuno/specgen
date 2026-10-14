// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品詳細
// source: detail-screen-spec.md
export interface Manufacturer {
  id: number;
  name: string;
}

export interface Component {
  id: number;
  name: string;
  quantity: number;
}

export interface ProductDetail {
  id: number;
  name: string;
  status: string;
  manufacturer: Manufacturer;
  components: Component[];
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
  manufacturer: Manufacturer;
  components: Component[];
}

export const productDetailCodes = {
  "CODE-001": {
    new: "新規",
    closed: "完了",
  },
} as const;

