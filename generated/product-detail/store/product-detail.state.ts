// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品詳細
// source: detail-screen-spec.md
import type {
  ProductDetail,
} from "../models/product-detail.models";

export const productDetailFeatureKey = "productDetail";

export interface ProductDetailState {
  data: {
    product: ProductDetail;
  };
}

// state_types に初期値の項目はない。数値 0、文字列 ""、真偽値 false、配列 [] は型のゼロ値であり、画面仕様の初期値ではない。
export const initialProductDetailState: ProductDetailState = {
  data: {
    product: {
      id: 0,
      name: "",
      status: "",
      manufacturer: {
        id: 0,
        name: "",
      },
      components: [],
    },
  },
};
