// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品更新
// source: edit-screen-spec.md
import { Component, Signal, signal, inject } from "@angular/core";
import { takeUntilDestroyed } from "@angular/core/rxjs-interop";
import { ActivatedRoute, Router } from "@angular/router";
import { Actions, ofType } from "@ngrx/effects";
import { Store } from "@ngrx/store";

import type { ProductUpdateRequest, StatusOption } from "../models/product-update.models";
import { productUpdate, productUpdateSuccess, productUpdateFailure } from "../store/product-update.actions";
import { selectOptionsOpt001 } from "../store/product-update.selectors";
import { ProductUpdateForm } from "../form/product-update-form.form";

/** 操作 */
@Component({
  selector: "app-product-update-actions",
  templateUrl: "./product-update-actions.component.html",
  standalone: false,
})
export class ProductUpdateActionsComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly queryForm = inject(ProductUpdateForm);
  private readonly store = inject(Store);
  private readonly optionsOpt001: Signal<StatusOption[]> = this.store.selectSignal(
    selectOptionsOpt001,
  );
  protected readonly saveButtonLoading = signal(false);

  constructor() {
    inject(Actions)
      .pipe(ofType(productUpdate), takeUntilDestroyed())
      .subscribe(() => {
        this.saveButtonLoading.set(true);
      });
    inject(Actions)
      .pipe(
        ofType(productUpdateSuccess, productUpdateFailure),
        takeUntilDestroyed(),
      )
      .subscribe(() => {
        this.saveButtonLoading.set(false);
      });
  }

  protected saveButtonDisabled(): boolean {
    return !this.queryForm.isValid(this.optionsOpt001()) || this.saveButtonLoading();
  }

  protected saveButton(): void {
    if (this.saveButtonLoading()) {
      return;
    }
    if (!this.queryForm.validate(this.optionsOpt001())) {
      return;
    }
    const id = this.route.snapshot.paramMap.get("id");
    if (id === null || !/^(0|[1-9]\d*)$/.test(id)) {
      return;
    }
    const input = this.queryForm.form.getRawValue();
    const request: ProductUpdateRequest = {
      id: Number(id),
      name: input.productName,
      status: input.status,
    };
    this.store.dispatch(productUpdate(request));
  }

  protected cancelButton(): void {
    this.router.navigateByUrl("/products");
  }
}
