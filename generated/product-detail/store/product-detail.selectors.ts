// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品詳細
// source: detail-screen-spec.md
import { createFeatureSelector, createSelector } from "@ngrx/store";

import { productDetailFeatureKey } from "./product-detail.state";
import type { ProductDetailState } from "./product-detail.state";

export const selectProductDetailState = createFeatureSelector<ProductDetailState>(
  productDetailFeatureKey,
);

export const selectDataProduct = createSelector(
  selectProductDetailState,
  (state: ProductDetailState) => state.data.product,
);
