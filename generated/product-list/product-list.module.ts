// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
import { CommonModule } from "@angular/common";
import { provideHttpClient } from "@angular/common/http";
import { NgModule } from "@angular/core";
import { ReactiveFormsModule } from "@angular/forms";
import { EffectsModule } from "@ngrx/effects";
import { StoreModule } from "@ngrx/store";

import { ProductListQueryComponent } from "./query/product-list-query.component";
import { ProductListActionsComponent } from "./actions/product-list-actions.component";
import { ProductListListComponent } from "./list/product-list-list.component";
import { ProductListScreenComponent } from "./product-list.component";
import { ProductListQueryForm } from "./query/product-list-query.form";
import { ProductListApiService } from "./services/product-list-api.service";
import { ProductListEffects } from "./store/product-list.effects";
import { productListReducer } from "./store/product-list.reducer";
import { productListFeatureKey } from "./store/product-list.state";

@NgModule({
  declarations: [
    ProductListScreenComponent,
    ProductListQueryComponent,
    ProductListActionsComponent,
    ProductListListComponent,
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    StoreModule.forFeature(productListFeatureKey, productListReducer),
    EffectsModule.forFeature([ProductListEffects]),
  ],
  exports: [ProductListScreenComponent],
  providers: [provideHttpClient(), ProductListApiService, ProductListQueryForm],
})
export class ProductListModule {}
