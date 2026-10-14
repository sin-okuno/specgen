import { platformBrowser } from "@angular/platform-browser";
import "zone.js";

import { AppModule } from "../generated/app/app.module";

platformBrowser()
  .bootstrapModule(AppModule)
  .catch((error: unknown) => {
    console.error(error);
  });
