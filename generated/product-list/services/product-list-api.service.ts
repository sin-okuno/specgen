// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品一覧
// source: list-screen-spec.md
import { Injectable, inject } from "@angular/core";
import { HttpClient, HttpParams } from "@angular/common/http";
import type {
  ProductListRequest,
  ProductListResponse,
  ProductStatusOptionsResponse,
} from "../models/product-list.models";
import type { Observable } from "rxjs";

@Injectable()
export class ProductListApiService {
  private readonly http = inject(HttpClient);

  getProductList(request: ProductListRequest): Observable<ProductListResponse> {
    const url = "/api/products/";
    let params = new HttpParams();
    if (request.name !== undefined) {
      params = params.set("name", String(request.name));
    }
    if (request.status !== undefined) {
      params = params.set("status", String(request.status));
    }
    params = params.set("page", String(request.page));
    params = params.set("page_size", String(request.page_size));
    params = params.set("ordering", String(request.ordering));
    return this.http.get<ProductListResponse>(url, { params });
  }

  getProductStatusOptions(): Observable<ProductStatusOptionsResponse> {
    const url = "/api/products/options/";
    return this.http.get<ProductStatusOptionsResponse>(url);
  }
}
