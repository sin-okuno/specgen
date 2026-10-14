// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
import { Component, Signal, signal, inject } from "@angular/core";
import { takeUntilDestroyed } from "@angular/core/rxjs-interop";
import { Router } from "@angular/router";
import { Actions, ofType } from "@ngrx/effects";
import { Store } from "@ngrx/store";

import type { ProductListRequest, StatusOption } from "../models/product-list.models";
import { productList, setPaginationPage, productListSuccess, productListFailure } from "../store/product-list.actions";
import { selectProductListState, selectOptionsOpt001 } from "../store/product-list.selectors";
import type { ProductListState } from "../store/product-list.state";
import { ProductListQueryForm } from "../query/product-list-query.form";

/** 操作 */
@Component({
  selector: "app-product-list-actions",
  templateUrl: "./product-list-actions.component.html",
  standalone: false,
})
export class ProductListActionsComponent {
  private readonly router = inject(Router);
  private readonly queryForm = inject(ProductListQueryForm);
  private readonly store = inject(Store);
  private readonly state: Signal<ProductListState> = this.store.selectSignal(
    selectProductListState,
  );
  private readonly optionsOpt001: Signal<StatusOption[]> = this.store.selectSignal(
    selectOptionsOpt001,
  );
  protected readonly searchButtonLoading = signal(false);

  constructor() {
    inject(Actions)
      .pipe(ofType(productList), takeUntilDestroyed())
      .subscribe(() => {
        this.searchButtonLoading.set(true);
      });
    inject(Actions)
      .pipe(
        ofType(productListSuccess, productListFailure),
        takeUntilDestroyed(),
      )
      .subscribe(() => {
        this.searchButtonLoading.set(false);
      });
  }

  protected searchButtonDisabled(): boolean {
    return this.searchButtonLoading();
  }

  protected searchButton(): void {
    if (this.searchButtonLoading()) {
      return;
    }
    if (!this.queryForm.validate(this.optionsOpt001())) {
      return;
    }
    this.queryForm.applyQuery();
    const value = this.queryForm.applied();
    const state = this.state();
    this.store.dispatch(setPaginationPage({ page: 1 }));
    const request: ProductListRequest = {
      page: 1,
      page_size: state.pagination.pageSize,
      ordering: state.sort.ordering,
    };
    if (value.productName !== "") {
      request.name = value.productName;
    }
    if (value.status !== "") {
      request.status = value.status;
    }
    this.store.dispatch(productList(request));
  }

  protected createButton(): void {
    this.router.navigateByUrl("/products/new");
  }
}
