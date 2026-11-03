import { reactive } from "vue";
import { call } from "frappe-ui";

export const session = reactive({
	user: null,
	fullName: "",
	userImage: null,
	isManager: false,
	isSystemManager: false,
	frappeMeetAvailable: false,
	frappeCalendarAvailable: false,

	async init() {
		// Production gets boot from the Jinja page; the Vite dev server has to ask for it.
		let boot = typeof window.boot === "object" ? window.boot : null;
		if (!boot) {
			boot = await call("meeting.www.meeting.get_context_for_dev").catch(() => null);
		}
		if (!boot || boot.user === "Guest") {
			window.location.href = `/login?redirect-to=${window.location.pathname}`;
			return;
		}
		this.user = boot.user;
		this.fullName = boot.full_name;
		this.userImage = boot.user_image;
		this.isManager = boot.is_manager;
		this.isSystemManager = boot.is_system_manager;
		this.frappeMeetAvailable = boot.frappe_meet_available;
		this.frappeCalendarAvailable = boot.frappe_calendar_available;
	},

	async logout() {
		await call("logout");
		window.location.href = "/login";
	},
});
