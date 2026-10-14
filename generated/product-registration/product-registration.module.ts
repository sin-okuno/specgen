// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品登録
// source: create-screen-spec.md
import { CommonModule } from "@angular/common";
import { provideHttpClient } from "@angular/common/http";
import { NgModule } from "@angular/core";
import { ReactiveFormsModule } from "@angular/forms";
import { EffectsModule } from "@ngrx/effects";
import { StoreModule } from "@ngrx/store";

import { ProductRegistrationFormComponent } from "./form/product-registration-form.component";
import { ProductRegistrationActionsComponent } from "./actions/product-registration-actions.component";
import { ProductRegistrationScreenComponent } from "./product-registration.component";
import { ProductRegistrationForm } from "./form/product-registration-form.form";
import { ProductRegistrationApiService } from "./services/product-registration-api.service";
import { ProductRegistrationEffects } from "./store/product-registration.effects";
import { productRegistrationReducer } from "./store/product-registration.reducer";
import { productRegistrationFeatureKey } from "./store/product-registration.state";

@NgModule({
  declarations: [
    ProductRegistrationScreenComponent,
    ProductRegistrationFormComponent,
    ProductRegistrationActionsComponent,
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    StoreModule.forFeature(productRegistrationFeatureKey, productRegistrationReducer),
    EffectsModule.forFeature([ProductRegistrationEffects]),
  ],
  exports: [ProductRegistrationScreenComponent],
  providers: [provideHttpClient(), ProductRegistrationApiService, ProductRegistrationForm],
})
export class ProductRegistrationModule {}
