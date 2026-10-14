// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品詳細
// source: detail-screen-spec.md
import { Component, inject } from "@angular/core";
import { ActivatedRoute, Router } from "@angular/router";


/** 操作 */
@Component({
  selector: "app-product-detail-actions",
  templateUrl: "./product-detail-actions.component.html",
  standalone: false,
})
export class ProductDetailActionsComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  protected editButton(): void {
    const id = this.route.snapshot.paramMap.get("id");
    if (id === null || !/^(0|[1-9]\d*)$/.test(id)) {
      return;
    }
    this.router.navigateByUrl("/products/" + encodeURIComponent(id) + "/edit");
  }

  protected backButton(): void {
    this.router.navigateByUrl("/products");
  }
}
