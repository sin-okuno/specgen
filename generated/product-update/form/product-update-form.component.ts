// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品更新
// source: edit-screen-spec.md
import { Component, Signal, inject } from "@angular/core";
import { Store } from "@ngrx/store";

import type { StatusOption } from "../models/product-update.models";
import { selectOptionsOpt001 } from "../store/product-update.selectors";
import { ProductUpdateForm } from "./product-update-form.form";

/** 製品情報 */
@Component({
  selector: "app-product-update-form",
  templateUrl: "./product-update-form.component.html",
  standalone: false,
})
export class ProductUpdateFormComponent {
  protected readonly queryForm = inject(ProductUpdateForm);
  private readonly store = inject(Store);
  protected readonly optionsOpt001: Signal<StatusOption[]> = this.store.selectSignal(
    selectOptionsOpt001,
  );
}
