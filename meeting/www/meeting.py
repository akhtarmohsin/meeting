import frappe

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + frappe.request.path
		raise frappe.Redirect
	# The SPA sends this back on every POST; without it Frappe rejects calls with a 400.
	context.csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()  # persist the token on the session before the page is served
	context.boot = get_boot()


@frappe.whitelist(methods=["POST"])
def get_context_for_dev() -> dict:
	if not frappe.conf.developer_mode:
		frappe.throw("Only available in developer mode")
	return get_boot()


def get_boot() -> dict:
	user = frappe.session.user
	return frappe._dict(
		user=user,
		full_name=frappe.utils.get_fullname(user),
		user_image=frappe.db.get_value("User", user, "user_image"),
		is_manager=bool({"System Manager", "Meeting Manager"} & set(frappe.get_roles())),
		site_name=frappe.local.site,
		time_zone=frappe.utils.get_system_timezone(),
	)
