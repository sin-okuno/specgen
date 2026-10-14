// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品更新
// source: edit-screen-spec.md
import { CommonModule } from "@angular/common";
import { provideHttpClient } from "@angular/common/http";
import { NgModule } from "@angular/core";
import { ReactiveFormsModule } from "@angular/forms";
import { EffectsModule } from "@ngrx/effects";
import { StoreModule } from "@ngrx/store";

import { ProductUpdateFormComponent } from "./form/product-update-form.component";
import { ProductUpdateActionsComponent } from "./actions/product-update-actions.component";
import { ProductUpdateScreenComponent } from "./product-update.component";
import { ProductUpdateForm } from "./form/product-update-form.form";
import { ProductUpdateApiService } from "./services/product-update-api.service";
import { ProductUpdateEffects } from "./store/product-update.effects";
import { productUpdateReducer } from "./store/product-update.reducer";
import { productUpdateFeatureKey } from "./store/product-update.state";

@NgModule({
  declarations: [
    ProductUpdateScreenComponent,
    ProductUpdateFormComponent,
    ProductUpdateActionsComponent,
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    StoreModule.forFeature(productUpdateFeatureKey, productUpdateReducer),
    EffectsModule.forFeature([ProductUpdateEffects]),
  ],
  exports: [ProductUpdateScreenComponent],
  providers: [provideHttpClient(), ProductUpdateApiService, ProductUpdateForm],
})
export class ProductUpdateModule {}
