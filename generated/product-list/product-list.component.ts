// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
import { Component, OnInit, inject } from "@angular/core";
import { Store } from "@ngrx/store";

import { initializeProductList } from "./store/product-list.actions";

@Component({
  selector: "app-product-list",
  templateUrl: "./product-list.component.html",
  standalone: false,
})
export class ProductListScreenComponent implements OnInit {
  private readonly store = inject(Store);

  ngOnInit(): void {
    this.store.dispatch(initializeProductList());
  }
}
