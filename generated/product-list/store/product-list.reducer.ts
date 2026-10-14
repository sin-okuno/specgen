// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
import { createReducer, on } from "@ngrx/store";
import {
  setPaginationPage,
  setPaginationPageSize,
  setSortOrdering,
  productListSuccess,
  productStatusOptionsSuccess,
} from "./product-list.actions";
import { initialProductListState } from "./product-list.state";
import type { ProductListState } from "./product-list.state";
import type {
  ProductListResponse,
  ProductStatusOptionsResponse,
} from "../models/product-list.models";

export const productListReducer = createReducer(
  initialProductListState,
  on(setPaginationPage, (state: ProductListState, action: { page: number }): ProductListState =>
  ({
    ...state,
    pagination: {
      ...state.pagination,
      page: action.page,
    },
  })),
  on(setPaginationPageSize, (state: ProductListState, action: { pageSize: number }): ProductListState =>
  ({
    ...state,
    pagination: {
      ...state.pagination,
      pageSize: action.pageSize,
    },
  })),
  on(setSortOrdering, (state: ProductListState, action: { ordering: string }): ProductListState =>
  ({
    ...state,
    sort: {
      ...state.sort,
      ordering: action.ordering,
    },
  })),
  on(productListSuccess, (state: ProductListState, action: { body: ProductListResponse }): ProductListState =>
  ({
    ...state,
    list: {
      ...state.list,
      items: action.body.results,
    },
    pagination: {
      ...state.pagination,
      total: action.body.count,
    },
  })),
  on(productStatusOptionsSuccess, (state: ProductListState, action: { body: ProductStatusOptionsResponse }): ProductListState =>
  ({
    ...state,
    options: {
      ...state.options,
      "OPT-001": action.body.statuses,
    },
  }))
);
