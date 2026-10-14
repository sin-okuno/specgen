// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品更新
// source: edit-screen-spec.md
import { Component, OnInit, inject } from "@angular/core";
import { ActivatedRoute } from "@angular/router";
import { Store } from "@ngrx/store";

import { initializeProductUpdate } from "./store/product-update.actions";

@Component({
  selector: "app-product-update",
  templateUrl: "./product-update.component.html",
  standalone: false,
})
export class ProductUpdateScreenComponent implements OnInit {
  private readonly store = inject(Store);
  private readonly route = inject(ActivatedRoute);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get("id");
    if (id === null || !/^(0|[1-9]\d*)$/.test(id)) {
      return;
    }
    this.store.dispatch(initializeProductUpdate({
      id: Number(id),
    }));
  }
}
