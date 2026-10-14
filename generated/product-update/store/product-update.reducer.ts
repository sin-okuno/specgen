// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品更新
// source: edit-screen-spec.md
import { createReducer, on } from "@ngrx/store";
import {
  productStatusOptionsSuccess,
  productUpdateSuccess,
} from "./product-update.actions";
import { initialProductUpdateState } from "./product-update.state";
import type { ProductUpdateState } from "./product-update.state";
import type {
  ProductStatusOptionsResponse,
  ProductUpdateResponse,
} from "../models/product-update.models";

export const productUpdateReducer = createReducer(
  initialProductUpdateState,
  on(productStatusOptionsSuccess, (state: ProductUpdateState, action: { body: ProductStatusOptionsResponse }): ProductUpdateState =>
  ({
    ...state,
    options: {
      ...state.options,
      "OPT-001": action.body.statuses,
    },
  })),
  on(productUpdateSuccess, (state: ProductUpdateState, action: { body: ProductUpdateResponse }): ProductUpdateState =>
  ({
    ...state,
    data: {
      ...state.data,
      product: {
        ...state.data.product,
        id: action.body.id,
      },
    },
  }))
);
