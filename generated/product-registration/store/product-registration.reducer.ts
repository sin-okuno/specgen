// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品登録
// source: create-screen-spec.md
import { createReducer, on } from "@ngrx/store";
import {
  productRegistrationSuccess,
  productStatusOptionsSuccess,
} from "./product-registration.actions";
import { initialProductRegistrationState } from "./product-registration.state";
import type { ProductRegistrationState } from "./product-registration.state";
import type {
  ProductRegistrationResponse,
  ProductStatusOptionsResponse,
} from "../models/product-registration.models";

export const productRegistrationReducer = createReducer(
  initialProductRegistrationState,
  on(productRegistrationSuccess, (state: ProductRegistrationState, action: { body: ProductRegistrationResponse }): ProductRegistrationState =>
  ({
    ...state,
    data: {
      ...state.data,
      product: {
        ...state.data.product,
        id: action.body.id,
      },
    },
  })),
  on(productStatusOptionsSuccess, (state: ProductRegistrationState, action: { body: ProductStatusOptionsResponse }): ProductRegistrationState =>
  ({
    ...state,
    options: {
      ...state.options,
      "OPT-001": action.body.statuses,
    },
  }))
);
