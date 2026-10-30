import frappe

MANAGER_ROLES = {"System Manager", "Meeting Manager"}


def has_app_permission() -> bool:
	if frappe.session.user == "Administrator":
		return True
	return bool(MANAGER_ROLES.union({"Meeting User"}) & set(frappe.get_roles()))


def is_manager(user: str | None = None) -> bool:
	return bool(MANAGER_ROLES & set(frappe.get_roles(user)))


def meeting_query(user: str | None = None) -> str:
	"""Meeting Users only see meetings they organize or are invited to."""
	user = user or frappe.session.user
	if is_manager(user):
		return ""
	user = frappe.db.escape(user)
	return f"""(`tabMeeting`.organizer = {user} or exists (
		select 1 from `tabMeeting Attendee` a
		where a.parent = `tabMeeting`.name and a.parenttype = 'Meeting'
		and (a.user = {user} or a.email = {user})))"""


def meeting_has_permission(doc, ptype: str = "read", user: str | None = None) -> bool:
	user = user or frappe.session.user
	if is_manager(user) or doc.organizer == user:
		return True
	if ptype in ("write", "delete", "cancel"):
		return False
	return any(user in (row.user, row.email) for row in doc.attendees)


def action_item_query(user: str | None = None) -> str:
	user = user or frappe.session.user
	if is_manager(user):
		return ""
	visible_meetings = meeting_query(user)
	user = frappe.db.escape(user)
	return f"""(`tabMeeting Action Item`.assigned_to = {user}
		or `tabMeeting Action Item`.owner = {user}
		or `tabMeeting Action Item`.meeting in (select name from `tabMeeting` where {visible_meetings}))"""


def action_item_has_permission(doc, ptype: str = "read", user: str | None = None) -> bool:
	user = user or frappe.session.user
	if is_manager(user) or user in (doc.assigned_to, doc.owner):
		return True
	if not doc.meeting:
		return False
	return frappe.get_doc("Meeting", doc.meeting).has_permission("read", user=user)
