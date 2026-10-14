// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品登録
// source: create-screen-spec.md
import { Injectable, inject } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import type {
  ProductRegistrationRequest,
  ProductRegistrationResponse,
  ProductStatusOptionsResponse,
} from "../models/product-registration.models";
import type { Observable } from "rxjs";

@Injectable()
export class ProductRegistrationApiService {
  private readonly http = inject(HttpClient);

  postProductRegistration(request: ProductRegistrationRequest): Observable<ProductRegistrationResponse> {
    const url = "/api/products/";
    const body = {
      name: request.name,
      status: request.status,
    };
    return this.http.post<ProductRegistrationResponse>(url, body);
  }

  getProductStatusOptions(): Observable<ProductStatusOptionsResponse> {
    const url = "/api/products/options/";
    return this.http.get<ProductStatusOptionsResponse>(url);
  }
}
