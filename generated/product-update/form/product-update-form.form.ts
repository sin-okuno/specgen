// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品更新
// source: edit-screen-spec.md
import { Injectable, signal } from "@angular/core";
import { FormControl, FormGroup } from "@angular/forms";
import type { StatusOption } from "../models/product-update.models";

@Injectable()
export class ProductUpdateForm {
  readonly form = new FormGroup({
    productName: new FormControl<string>("", { nonNullable: true }),
    status: new FormControl<string>("", { nonNullable: true }),
  });
  readonly applied = signal(this.form.getRawValue());
  readonly messages = signal<Readonly<Record<string, string>>>({});

  applyQuery(): void {
    this.applied.set(this.form.getRawValue());
  }

  validate(optionsOpt001: readonly StatusOption[]): boolean {
    const value = this.form.getRawValue();
    const messages: Record<string, string> = {};
    if (value.productName === "") {
      messages["productName"] = "製品名を1〜100文字で入力してください";
    } else if (value.productName.length > 100) {
      messages["productName"] = "製品名を1〜100文字で入力してください";
    }
    const statusIsKnown = optionsOpt001.some((option) => option.value === value.status);
    if (value.status === "") {
      messages["status"] = "状態を選択してください";
    } else if (value.status !== "" && !statusIsKnown) {
      messages["status"] = "状態を選択してください";
    }
    this.messages.set(messages);
    return Object.keys(messages).length === 0;
  }

  isValid(optionsOpt001: readonly StatusOption[]): boolean {
    const value = this.form.getRawValue();
    if (value.productName === "") {
      return false;
    }
    if (value.productName.length > 100) {
      return false;
    }
    const statusIsKnown = optionsOpt001.some((option) => option.value === value.status);
    if (value.status === "") {
      return false;
    }
    if (value.status !== "" && !statusIsKnown) {
      return false;
    }
    return true;
  }
}
