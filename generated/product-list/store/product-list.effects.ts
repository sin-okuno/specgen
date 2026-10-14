// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
import { Injectable, inject } from "@angular/core";
import { Actions, createEffect, ofType } from "@ngrx/effects";
import { Store } from "@ngrx/store";
import { of } from "rxjs";
import { catchError, map, mergeMap, switchMap, withLatestFrom } from "rxjs/operators";

import { ProductListApiService } from "../services/product-list-api.service";
import type {
  ProductListRequest,
  ProductListResponse,
  ProductStatusOptionsResponse,
} from "../models/product-list.models";
import {
  initializeProductList,
  productList,
  productListSuccess,
  productListFailure,
  productStatusOptions,
  productStatusOptionsSuccess,
  productStatusOptionsFailure,
} from "./product-list.actions";
import type { ProductListState } from "./product-list.state";
import { selectProductListState } from "./product-list.selectors";

@Injectable()
export class ProductListEffects {
  private readonly actions$ = inject(Actions);
  private readonly api = inject(ProductListApiService);
  private readonly store = inject(Store);

  readonly initializeProductList$ = createEffect(() =>
    this.actions$.pipe(
      ofType(initializeProductList),
      withLatestFrom(this.store.select(selectProductListState)),
      mergeMap(([, state]: [unknown, ProductListState]) => [
        productStatusOptions(),
        productList({
          page: state.pagination.page,
          page_size: state.pagination.pageSize,
          ordering: state.sort.ordering,
        }),
      ]),
    ),
  );

  readonly productList$ = createEffect(() =>
    this.actions$.pipe(
      ofType(productList),
      switchMap((action: ProductListRequest) =>
        this.api.getProductList(action).pipe(
          map((body: ProductListResponse) => productListSuccess({ body })),
          catchError((error: unknown) =>
            of(
              productListFailure({
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
}
