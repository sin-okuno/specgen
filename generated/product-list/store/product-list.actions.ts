// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
import { createAction, props } from "@ngrx/store";
import type {
  ProductListResponse,
  ProductStatusOptionsResponse,
} from "../models/product-list.models";

export const initializeProductList = createAction("[Product List] Initialize");

export const setPaginationPage = createAction(
  "[Product List] Set Pagination Page",
  props<{
    page: number;
  }>()
);

export const setPaginationPageSize = createAction(
  "[Product List] Set Pagination Page Size",
  props<{
    pageSize: number;
  }>()
);

export const setSortOrdering = createAction(
  "[Product List] Set Sort Ordering",
  props<{
    ordering: string;
  }>()
);

export const productList = createAction(
  "[Product List] Product List",
  props<{
    name?: string;
    status?: string;
    page: number;
    page_size: number;
    ordering: string;
  }>()
);

export const productListSuccess = createAction(
  "[Product List] Product List Success",
  props<{
    body: ProductListResponse;
  }>()
);

export const productListFailure = createAction(
  "[Product List] Product List Failure",
  props<{
    message: string;
  }>()
);

export const productStatusOptions = createAction("[Product List] Product Status Options");

export const productStatusOptionsSuccess = createAction(
  "[Product List] Product Status Options Success",
  props<{
    body: ProductStatusOptionsResponse;
  }>()
);

export const productStatusOptionsFailure = createAction(
  "[Product List] Product Status Options Failure",
  props<{
    message: string;
  }>()
);
