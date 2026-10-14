// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品登録
// source: create-screen-spec.md
import { createAction, props } from "@ngrx/store";
import type {
  ProductRegistrationResponse,
  ProductStatusOptionsResponse,
} from "../models/product-registration.models";

export const initializeProductRegistration = createAction("[Product Registration] Initialize");

export const productRegistration = createAction(
  "[Product Registration] Product Registration",
  props<{
    name: string;
    status: string;
  }>()
);

export const productRegistrationSuccess = createAction(
  "[Product Registration] Product Registration Success",
  props<{
    body: ProductRegistrationResponse;
  }>()
);

export const productRegistrationFailure = createAction(
  "[Product Registration] Product Registration Failure",
  props<{
    message: string;
  }>()
);

export const productStatusOptions = createAction("[Product Registration] Product Status Options");

export const productStatusOptionsSuccess = createAction(
  "[Product Registration] Product Status Options Success",
  props<{
    body: ProductStatusOptionsResponse;
  }>()
);

export const productStatusOptionsFailure = createAction(
  "[Product Registration] Product Status Options Failure",
  props<{
    message: string;
  }>()
);
