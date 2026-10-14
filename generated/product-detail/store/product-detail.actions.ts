// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品詳細
// source: detail-screen-spec.md
import { createAction, props } from "@ngrx/store";
import type {
  ProductDetailResponse,
} from "../models/product-detail.models";

export const initializeProductDetail = createAction(
  "[Product Detail] Initialize",
  props<{
    id: number;
  }>()
);

export const productDetail = createAction(
  "[Product Detail] Product Detail",
  props<{
    id: number;
  }>()
);

export const productDetailSuccess = createAction(
  "[Product Detail] Product Detail Success",
  props<{
    body: ProductDetailResponse;
  }>()
);

export const productDetailFailure = createAction(
  "[Product Detail] Product Detail Failure",
  props<{
    message: string;
  }>()
);
