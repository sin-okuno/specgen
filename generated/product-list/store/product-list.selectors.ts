// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
import { createFeatureSelector, createSelector } from "@ngrx/store";

import { productListFeatureKey } from "./product-list.state";
import type { ProductListState } from "./product-list.state";

export const selectProductListState = createFeatureSelector<ProductListState>(
  productListFeatureKey,
);

export const selectListItems = createSelector(
  selectProductListState,
  (state: ProductListState) => state.list.items,
);

export const selectPaginationPage = createSelector(
  selectProductListState,
  (state: ProductListState) => state.pagination.page,
);

export const selectPaginationPageSize = createSelector(
  selectProductListState,
  (state: ProductListState) => state.pagination.pageSize,
);

export const selectPaginationTotal = createSelector(
  selectProductListState,
  (state: ProductListState) => state.pagination.total,
);

export const selectSortOrdering = createSelector(
  selectProductListState,
  (state: ProductListState) => state.sort.ordering,
);

export const selectOptionsOpt001 = createSelector(
  selectProductListState,
  (state: ProductListState) => state.options["OPT-001"],
);
