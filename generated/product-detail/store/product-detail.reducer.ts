// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品詳細
// source: detail-screen-spec.md
import { createReducer, on } from "@ngrx/store";
import {
  productDetailSuccess,
} from "./product-detail.actions";
import { initialProductDetailState } from "./product-detail.state";
import type { ProductDetailState } from "./product-detail.state";
import type {
  ProductDetailResponse,
} from "../models/product-detail.models";

export const productDetailReducer = createReducer(
  initialProductDetailState,
  on(productDetailSuccess, (state: ProductDetailState, action: { body: ProductDetailResponse }): ProductDetailState =>
  ({
    ...state,
    data: {
      ...state.data,
      product: {
        ...state.data.product,
        id: action.body.id,
        name: action.body.name,
        status: action.body.status,
        manufacturer: action.body.manufacturer,
        components: action.body.components,
      },
    },
  }))
);
