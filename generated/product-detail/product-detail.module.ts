// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品詳細
// source: detail-screen-spec.md
import { CommonModule } from "@angular/common";
import { provideHttpClient } from "@angular/common/http";
import { NgModule } from "@angular/core";
import { ReactiveFormsModule } from "@angular/forms";
import { EffectsModule } from "@ngrx/effects";
import { StoreModule } from "@ngrx/store";

import { ProductDetailDetailComponent } from "./detail/product-detail-detail.component";
import { ProductDetailActionsComponent } from "./actions/product-detail-actions.component";
import { ProductDetailScreenComponent } from "./product-detail.component";
import { ProductDetailApiService } from "./services/product-detail-api.service";
import { ProductDetailEffects } from "./store/product-detail.effects";
import { productDetailReducer } from "./store/product-detail.reducer";
import { productDetailFeatureKey } from "./store/product-detail.state";

@NgModule({
  declarations: [
    ProductDetailScreenComponent,
    ProductDetailDetailComponent,
    ProductDetailActionsComponent,
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    StoreModule.forFeature(productDetailFeatureKey, productDetailReducer),
    EffectsModule.forFeature([ProductDetailEffects]),
  ],
  exports: [ProductDetailScreenComponent],
  providers: [provideHttpClient(), ProductDetailApiService],
})
export class ProductDetailModule {}
