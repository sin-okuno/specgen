// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品詳細
// source: detail-screen-spec.md
import { Injectable, inject } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import type {
  ProductDetailRequest,
  ProductDetailResponse,
} from "../models/product-detail.models";
import type { Observable } from "rxjs";

@Injectable()
export class ProductDetailApiService {
  private readonly http = inject(HttpClient);

  getProductDetail(request: ProductDetailRequest): Observable<ProductDetailResponse> {
    let url = "/api/products/{id}/";
    url = url.split("{id}").join(encodeURIComponent(String(request.id)));
    return this.http.get<ProductDetailResponse>(url);
  }
}
