// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品登録
// source: create-screen-spec.md
import { createFeatureSelector, createSelector } from "@ngrx/store";

import { productRegistrationFeatureKey } from "./product-registration.state";
import type { ProductRegistrationState } from "./product-registration.state";

export const selectProductRegistrationState = createFeatureSelector<ProductRegistrationState>(
  productRegistrationFeatureKey,
);

export const selectDataProductId = createSelector(
  selectProductRegistrationState,
  (state: ProductRegistrationState) => state.data.product.id,
);

export const selectOptionsOpt001 = createSelector(
  selectProductRegistrationState,
  (state: ProductRegistrationState) => state.options["OPT-001"],
);
