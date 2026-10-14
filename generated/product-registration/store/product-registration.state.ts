// Generated from Screen Model schema 0.3. Phase 1 scaffold.
// screen: 製品登録
// source: create-screen-spec.md
import type {
  StatusOption,
} from "../models/product-registration.models";

export const productRegistrationFeatureKey = "productRegistration";

export interface ProductRegistrationState {
  data: {
    product: {
      id: number;
    };
  };
  options: {
    "OPT-001": StatusOption[];
  };
}

// state_types に初期値の項目はない。数値 0、文字列 ""、真偽値 false、配列 [] は型のゼロ値であり、画面仕様の初期値ではない。
export const initialProductRegistrationState: ProductRegistrationState = {
  data: {
    product: {
      id: 0,
    },
  },
  options: {
    "OPT-001": [],
  },
};
