import { createApp } from "vue";
import { setConfig, frappeRequest, resourcesPlugin } from "frappe-ui";
import App from "./App.vue";
import router from "./router";
import { session } from "./data/session";
import "./main.css";

setConfig("resourceFetcher", frappeRequest);

const app = createApp(App);
app.use(resourcesPlugin);
app.use(router);

session
	.init()
	.then(() => router.isReady())
	.then(() => app.mount("#app"));
