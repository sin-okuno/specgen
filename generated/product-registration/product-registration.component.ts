// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品登録
// source: create-screen-spec.md
import { Component, OnInit, inject } from "@angular/core";
import { Store } from "@ngrx/store";

import { initializeProductRegistration } from "./store/product-registration.actions";

@Component({
  selector: "app-product-registration",
  templateUrl: "./product-registration.component.html",
  standalone: false,
})
export class ProductRegistrationScreenComponent implements OnInit {
  private readonly store = inject(Store);

  ngOnInit(): void {
    this.store.dispatch(initializeProductRegistration());
  }
}
