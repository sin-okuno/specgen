// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品登録
// source: create-screen-spec.md
import { Component, Signal, signal, inject } from "@angular/core";
import { takeUntilDestroyed } from "@angular/core/rxjs-interop";
import { Router } from "@angular/router";
import { Actions, ofType } from "@ngrx/effects";
import { Store } from "@ngrx/store";

import type { ProductRegistrationRequest, StatusOption } from "../models/product-registration.models";
import { productRegistration, productRegistrationSuccess, productRegistrationFailure } from "../store/product-registration.actions";
import { selectOptionsOpt001 } from "../store/product-registration.selectors";
import { ProductRegistrationForm } from "../form/product-registration-form.form";

/** 操作 */
@Component({
  selector: "app-product-registration-actions",
  templateUrl: "./product-registration-actions.component.html",
  standalone: false,
})
export class ProductRegistrationActionsComponent {
  private readonly router = inject(Router);
  private readonly queryForm = inject(ProductRegistrationForm);
  private readonly store = inject(Store);
  private readonly optionsOpt001: Signal<StatusOption[]> = this.store.selectSignal(
    selectOptionsOpt001,
  );
  protected readonly saveButtonSubmitting = signal(false);

  constructor() {
    inject(Actions)
      .pipe(
        ofType(productRegistrationSuccess, productRegistrationFailure),
        takeUntilDestroyed(),
      )
      .subscribe(() => {
        this.saveButtonSubmitting.set(false);
      });
  }

  protected saveButtonDisabled(): boolean {
    return !this.queryForm.isValid(this.optionsOpt001()) || this.saveButtonSubmitting();
  }

  protected saveButton(): void {
    if (this.saveButtonSubmitting()) {
      return;
    }
    if (!this.queryForm.validate(this.optionsOpt001())) {
      return;
    }
    const input = this.queryForm.form.getRawValue();
    const request: ProductRegistrationRequest = {
      name: input.productName,
      status: input.status,
    };
    this.saveButtonSubmitting.set(true);
    this.store.dispatch(productRegistration(request));
  }

  protected cancelButton(): void {
    this.router.navigateByUrl("/products");
  }
}
