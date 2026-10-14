// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品登録
// source: create-screen-spec.md
import { Injectable, inject } from "@angular/core";
import { Router } from "@angular/router";
import { Actions, createEffect, ofType } from "@ngrx/effects";
import { Store } from "@ngrx/store";
import { of } from "rxjs";
import { catchError, map, mergeMap, switchMap, tap, withLatestFrom } from "rxjs/operators";

import { ProductRegistrationApiService } from "../services/product-registration-api.service";
import type {
  ProductRegistrationRequest,
  ProductRegistrationResponse,
  ProductStatusOptionsResponse,
} from "../models/product-registration.models";
import {
  initializeProductRegistration,
  productRegistration,
  productRegistrationSuccess,
  productRegistrationFailure,
  productStatusOptions,
  productStatusOptionsSuccess,
  productStatusOptionsFailure,
} from "./product-registration.actions";
import type { ProductRegistrationState } from "./product-registration.state";
import { selectProductRegistrationState } from "./product-registration.selectors";

@Injectable()
export class ProductRegistrationEffects {
  private readonly actions$ = inject(Actions);
  private readonly api = inject(ProductRegistrationApiService);
  private readonly router = inject(Router);
  private readonly store = inject(Store);

  readonly initializeProductRegistration$ = createEffect(() =>
    this.actions$.pipe(
      ofType(initializeProductRegistration),
      withLatestFrom(this.store.select(selectProductRegistrationState)),
      mergeMap(([, state]: [unknown, ProductRegistrationState]) => [
        productStatusOptions(),
      ]),
    ),
  );

  readonly productRegistration$ = createEffect(() =>
    this.actions$.pipe(
      ofType(productRegistration),
      switchMap((action: ProductRegistrationRequest) =>
        this.api.postProductRegistration(action).pipe(
          map((body: ProductRegistrationResponse) => productRegistrationSuccess({ body })),
          catchError((error: unknown) =>
            of(
              productRegistrationFailure({
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

  readonly navigateAfterProductRegistration$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(productRegistrationSuccess),
        tap(() => {
          this.router.navigateByUrl("/products");
        }),
      ),
    { dispatch: false },
  );
}
