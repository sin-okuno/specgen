// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品登録
// source: create-screen-spec.md
import { Component, Signal, inject } from "@angular/core";
import { Store } from "@ngrx/store";

import type { StatusOption } from "../models/product-registration.models";
import { selectOptionsOpt001 } from "../store/product-registration.selectors";
import { ProductRegistrationForm } from "./product-registration-form.form";

/** 製品情報 */
@Component({
  selector: "app-product-registration-form",
  templateUrl: "./product-registration-form.component.html",
  standalone: false,
})
export class ProductRegistrationFormComponent {
  protected readonly queryForm = inject(ProductRegistrationForm);
  private readonly store = inject(Store);
  protected readonly optionsOpt001: Signal<StatusOption[]> = this.store.selectSignal(
    selectOptionsOpt001,
  );
}
