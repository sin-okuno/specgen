// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品詳細
// source: detail-screen-spec.md
import { Component, Signal, inject } from "@angular/core";
import { Store } from "@ngrx/store";

import { productDetailCodes, type ProductDetail } from "../models/product-detail.models";
import { selectDataProduct } from "../store/product-detail.selectors";

/** 製品情報 */
@Component({
  selector: "app-product-detail-detail",
  templateUrl: "./product-detail-detail.component.html",
  standalone: false,
})
export class ProductDetailDetailComponent {
  private readonly store = inject(Store);
  protected readonly product: Signal<ProductDetail> =
    this.store.selectSignal(selectDataProduct);

  protected codeLabel(group: string, code: string, empty: string): string {
    if (group === "CODE-001") {
      const table = productDetailCodes["CODE-001"];
      if (code === "new") {
        return table.new;
      }
      if (code === "closed") {
        return table.closed;
      }
    }
    return empty;
  }
}
