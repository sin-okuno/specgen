// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品詳細
// source: detail-screen-spec.md
import { Component, OnInit, inject } from "@angular/core";
import { ActivatedRoute } from "@angular/router";
import { Store } from "@ngrx/store";

import { initializeProductDetail } from "./store/product-detail.actions";

@Component({
  selector: "app-product-detail",
  templateUrl: "./product-detail.component.html",
  standalone: false,
})
export class ProductDetailScreenComponent implements OnInit {
  private readonly store = inject(Store);
  private readonly route = inject(ActivatedRoute);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get("id");
    if (id === null || !/^(0|[1-9]\d*)$/.test(id)) {
      return;
    }
    this.store.dispatch(initializeProductDetail({
      id: Number(id),
    }));
  }
}
