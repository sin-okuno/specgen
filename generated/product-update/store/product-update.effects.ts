// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品更新
// source: edit-screen-spec.md
import { Injectable, inject } from "@angular/core";
import { Router } from "@angular/router";
import { Actions, createEffect, ofType } from "@ngrx/effects";
import { forkJoin, of, race } from "rxjs";
import { catchError, map, mergeMap, switchMap, tap, take } from "rxjs/operators";

import { ProductUpdateApiService } from "../services/product-update-api.service";
import { ProductUpdateForm } from "../form/product-update-form.form";
import type {
  ProductDetailRequest,
  ProductDetailResponse,
  ProductStatusOptionsResponse,
  ProductUpdateRequest,
  ProductUpdateResponse,
} from "../models/product-update.models";
import {
  initializeProductUpdate,
  productDetail,
  productDetailSuccess,
  productDetailFailure,
  productStatusOptions,
  productStatusOptionsSuccess,
  productStatusOptionsFailure,
  productUpdate,
  productUpdateSuccess,
  productUpdateFailure,
} from "./product-update.actions";

@Injectable()
export class ProductUpdateEffects {
  private readonly actions$ = inject(Actions);
  private readonly api = inject(ProductUpdateApiService);
  private readonly screenForm = inject(ProductUpdateForm);
  private readonly router = inject(Router);

  readonly initializeProductUpdate$ = createEffect(() =>
    this.actions$.pipe(
      ofType(initializeProductUpdate),
      mergeMap((action: { id: number }) => [
        productDetail({ id: action.id }),
        productStatusOptions(),
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

  readonly productStatusOptions$ = createEffect(() =>
    this.actions$.pipe(
      ofType(productStatusOptions),
      switchMap(() =>
        this.api.getProductStatusOptions().pipe(
          map((body: ProductStatusOptionsResponse) => productStatusOptionsSuccess({ body })),
          catchError((error: unknown) =>
            of(
              productStatusOptionsFailure({
                message: error instanceof Error ? error.message : "",
              }),
            ),
          ),
        ),
      ),
    ),
  );

  readonly productUpdate$ = createEffect(() =>
    this.actions$.pipe(
      ofType(productUpdate),
      switchMap((action: ProductUpdateRequest) =>
        this.api.patchProductUpdate(action).pipe(
          map((body: ProductUpdateResponse) => productUpdateSuccess({ body })),
          catchError((error: unknown) =>
            of(
              productUpdateFailure({
                message: error instanceof Error ? error.message : "",
              }),
            ),
          ),
        ),
      ),
    ),
  );

  readonly fillProductDetail$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(productDetailSuccess),
        tap((action: { body: ProductDetailResponse }) => {
          this.screenForm.form.patchValue({
            productName: action.body.name,
            status: action.body.status,
          });
        }),
      ),
    { dispatch: false },
  );

  readonly markFormPristine$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(initializeProductUpdate),
        switchMap(() =>
          race(
            forkJoin([
              this.actions$.pipe(ofType(productDetailSuccess), take(1)),
              this.actions$.pipe(ofType(productStatusOptionsSuccess), take(1)),
            ]).pipe(
              tap(() => {
                this.screenForm.form.markAsPristine();
              }),
            ),
            this.actions$.pipe(
              ofType(productDetailFailure, productStatusOptionsFailure),
              take(1),
            ),
          ),
        ),
      ),
    { dispatch: false },
  );

  readonly navigateAfterProductUpdate$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(productUpdateSuccess),
        tap(() => {
          this.router.navigateByUrl("/products");
        }),
      ),
    { dispatch: false },
  );
}
