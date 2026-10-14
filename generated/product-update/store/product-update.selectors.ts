// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品更新
// source: edit-screen-spec.md
import { createFeatureSelector, createSelector } from "@ngrx/store";

import { productUpdateFeatureKey } from "./product-update.state";
import type { ProductUpdateState } from "./product-update.state";

export const selectProductUpdateState = createFeatureSelector<ProductUpdateState>(
  productUpdateFeatureKey,
);

export const selectDataProductId = createSelector(
  selectProductUpdateState,
  (state: ProductUpdateState) => state.data.product.id,
);

export const selectOptionsOpt001 = createSelector(
  selectProductUpdateState,
  (state: ProductUpdateState) => state.options["OPT-001"],
);
