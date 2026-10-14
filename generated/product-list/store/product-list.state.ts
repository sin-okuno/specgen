// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
import type {
  ProductSummary,
  StatusOption,
} from "../models/product-list.models";

export const productListFeatureKey = "productList";

export interface ProductListState {
  list: {
    items: ProductSummary[];
  };
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  sort: {
    ordering: string;
  };
  options: {
    "OPT-001": StatusOption[];
  };
}

// 11.1 の初期ページ、初期表示件数、初期ソートを state の初期値にする。それ以外は型のゼロ値。
export const initialProductListState: ProductListState = {
  list: {
    items: [],
  },
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },
  sort: {
    ordering: "updated_at DESC",
  },
  options: {
    "OPT-001": [],
  },
};
