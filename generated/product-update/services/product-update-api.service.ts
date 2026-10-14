// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品更新
// source: edit-screen-spec.md
import { Injectable, inject } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import type {
  ProductDetailRequest,
  ProductDetailResponse,
  ProductStatusOptionsResponse,
  ProductUpdateRequest,
  ProductUpdateResponse,
} from "../models/product-update.models";
import type { Observable } from "rxjs";

@Injectable()
export class ProductUpdateApiService {
  private readonly http = inject(HttpClient);

  getProductDetail(request: ProductDetailRequest): Observable<ProductDetailResponse> {
    let url = "/api/products/{id}/";
    url = url.split("{id}").join(encodeURIComponent(String(request.id)));
    return this.http.get<ProductDetailResponse>(url);
  }

  getProductStatusOptions(): Observable<ProductStatusOptionsResponse> {
    const url = "/api/products/options/";
    return this.http.get<ProductStatusOptionsResponse>(url);
  }

  patchProductUpdate(request: ProductUpdateRequest): Observable<ProductUpdateResponse> {
    let url = "/api/products/{id}/";
    url = url.split("{id}").join(encodeURIComponent(String(request.id)));
    const body = {
      name: request.name,
      status: request.status,
    };
    return this.http.patch<ProductUpdateResponse>(url, body);
  }
}
