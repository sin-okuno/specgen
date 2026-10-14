// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
import { Component, Signal, inject } from "@angular/core";
import { Store } from "@ngrx/store";

import type { StatusOption } from "../models/product-list.models";
import { selectOptionsOpt001 } from "../store/product-list.selectors";
import { ProductListQueryForm } from "./product-list-query.form";

/** 検索条件 */
@Component({
  selector: "app-product-list-query",
  templateUrl: "./product-list-query.component.html",
  standalone: false,
})
export class ProductListQueryComponent {
  protected readonly queryForm = inject(ProductListQueryForm);
  private readonly store = inject(Store);
  protected readonly optionsOpt001: Signal<StatusOption[]> = this.store.selectSignal(
    selectOptionsOpt001,
  );
}
