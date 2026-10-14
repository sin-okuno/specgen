// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品詳細
// source: detail-screen-spec.md
import { Injectable, inject } from "@angular/core";
import { Actions, createEffect, ofType } from "@ngrx/effects";
import { of } from "rxjs";
import { catchError, map, mergeMap, switchMap } from "rxjs/operators";

import { ProductDetailApiService } from "../services/product-detail-api.service";
import type {
  ProductDetailRequest,
  ProductDetailResponse,
} from "../models/product-detail.models";
import {
  initializeProductDetail,
  productDetail,
  productDetailSuccess,
  productDetailFailure,
} from "./product-detail.actions";

@Injectable()
export class ProductDetailEffects {
  private readonly actions$ = inject(Actions);
  private readonly api = inject(ProductDetailApiService);

  readonly initializeProductDetail$ = createEffect(() =>
    this.actions$.pipe(
      ofType(initializeProductDetail),
      mergeMap((action: { id: number }) => [
        productDetail({ id: action.id }),
      ]),
    ),
  );

  readonly productDetail$ = createEffect(() =>
    this.actions$.pipe(
      ofType(productDetail),
      switchMap((action: ProductDetailRequest) =>
        this.api.getProductDetail(action).pipe(
          map((body: ProductDetailResponse) => productDetailSuccess({ body })),
          catchError((error: unknown) =>
            of(
              productDetailFailure({
                message: error instanceof Error ? error.message : "",
              }),
            ),
          ),
        ),
      ),
    ),
  );
}
