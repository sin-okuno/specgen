// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品更新
// source: edit-screen-spec.md
import { createAction, props } from "@ngrx/store";
import type {
  ProductDetailResponse,
  ProductStatusOptionsResponse,
  ProductUpdateResponse,
} from "../models/product-update.models";

export const initializeProductUpdate = createAction(
  "[Product Update] Initialize",
  props<{
    id: number;
  }>()
);

export const productDetail = createAction(
  "[Product Update] Product Detail",
  props<{
    id: number;
  }>()
);

export const productDetailSuccess = createAction(
  "[Product Update] Product Detail Success",
  props<{
    body: ProductDetailResponse;
  }>()
);

export const productDetailFailure = createAction(
  "[Product Update] Product Detail Failure",
  props<{
    message: string;
  }>()
);

export const productStatusOptions = createAction("[Product Update] Product Status Options");

export const productStatusOptionsSuccess = createAction(
  "[Product Update] Product Status Options Success",
  props<{
    body: ProductStatusOptionsResponse;
  }>()
);

export const productStatusOptionsFailure = createAction(
  "[Product Update] Product Status Options Failure",
  props<{
    message: string;
  }>()
);

export const productUpdate = createAction(
  "[Product Update] Product Update",
  props<{
    id: number;
    name: string;
    status: string;
  }>()
);

export const productUpdateSuccess = createAction(
  "[Product Update] Product Update Success",
  props<{
    body: ProductUpdateResponse;
  }>()
);

export const productUpdateFailure = createAction(
  "[Product Update] Product Update Failure",
  props<{
    message: string;
  }>()
);
