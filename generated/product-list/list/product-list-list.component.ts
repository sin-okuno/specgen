// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
import { Component, Signal, inject, signal } from "@angular/core";
import { takeUntilDestroyed } from "@angular/core/rxjs-interop";
import { Router } from "@angular/router";
import { Actions, ofType } from "@ngrx/effects";
import { Store } from "@ngrx/store";

import { productListCodes, type ProductSummary } from "../models/product-list.models";
import type { ProductListRequest } from "../models/product-list.models";
import { productList, setPaginationPage, setPaginationPageSize, setSortOrdering, productListSuccess } from "../store/product-list.actions";
import { selectListItems, selectProductListState, selectPaginationPage, selectPaginationPageSize, selectSortOrdering } from "../store/product-list.selectors";
import type { ProductListState } from "../store/product-list.state";
import { ProductListQueryForm } from "../query/product-list-query.form";

/** 検索結果 */
@Component({
  selector: "app-product-list-list",
  templateUrl: "./product-list-list.component.html",
  standalone: false,
})
export class ProductListListComponent {
  private readonly store = inject(Store);
  private readonly router = inject(Router);
  private readonly queryForm = inject(ProductListQueryForm);
  private readonly state: Signal<ProductListState> = this.store.selectSignal(
    selectProductListState,
  );
  protected readonly pageSizes: readonly number[] = [20, 50, 100];
  protected readonly page = this.store.selectSignal(selectPaginationPage);
  protected readonly pageSize = this.store.selectSignal(selectPaginationPageSize);
  protected readonly ordering = this.store.selectSignal(selectSortOrdering);
  protected readonly items: Signal<ProductSummary[]> = this.store.selectSignal(
    selectListItems,
  );
  protected readonly listReceived = signal(false);

  constructor() {
    inject(Actions)
      .pipe(ofType(productListSuccess), takeUntilDestroyed())
      .subscribe(() => {
        this.listReceived.set(true);
      });
  }

  protected codeLabel(group: string, code: string, empty: string): string {
    if (group === "CODE-001") {
      const table = productListCodes["CODE-001"];
      if (code === "new") {
        return table.new;
      }
      if (code === "closed") {
        return table.closed;
      }
    }
    return empty;
  }

  protected openRow(id: number): void {
    this.router.navigateByUrl("/products" + "/" + encodeURIComponent(String(id)));
  }

  protected openRowEdit(id: number, event: Event): void {
    event.stopPropagation();
    this.router.navigateByUrl(
      "/products" + "/" + encodeURIComponent(String(id)) + "/edit",
    );
  }

  protected changePaginationPage(event: Event): void {
    const element = event.target;
    if (!(element instanceof HTMLInputElement)) {
      return;
    }
    const page = Number(element.value);
    if (!Number.isInteger(page)) {
      return;
    }
    const value = this.queryForm.applied();
    const state = this.state();
    this.store.dispatch(setPaginationPage({ page }));
    const request: ProductListRequest = {
      page: page,
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

  protected changePaginationPageSize(event: Event): void {
    const element = event.target;
    if (!(element instanceof HTMLSelectElement)) {
      return;
    }
    const pageSize = Number(element.value);
    if (!this.pageSizes.includes(pageSize)) {
      return;
    }
    const page = 1;
    const value = this.queryForm.applied();
    const state = this.state();
    this.store.dispatch(setPaginationPageSize({ pageSize }));
    this.store.dispatch(setPaginationPage({ page }));
    const request: ProductListRequest = {
      page: page,
      page_size: pageSize,
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

  protected changeSortOrdering(event: Event): void {
    const element = event.target;
    if (!(element instanceof HTMLInputElement)) {
      return;
    }
    const ordering = element.value;
    const page = 1;
    const value = this.queryForm.applied();
    const state = this.state();
    this.store.dispatch(setSortOrdering({ ordering }));
    this.store.dispatch(setPaginationPage({ page }));
    const request: ProductListRequest = {
      page: page,
      page_size: state.pagination.pageSize,
      ordering: ordering,
    };
    if (value.productName !== "") {
      request.name = value.productName;
    }
    if (value.status !== "") {
      request.status = value.status;
    }
    this.store.dispatch(productList(request));
  }
}
