import frappe
from frappe import _
from frappe.utils import validate_email_address

from meeting.permissions import is_manager

MEETING_ROLES = ("Meeting User", "Meeting Manager")


@frappe.whitelist()
def get_users() -> list[dict]:
	"""Everyone with a Meeting role, for the Settings → Users list."""
	check_manager()
	rows = frappe.get_all(
		"Has Role",
		filters={"role": ["in", MEETING_ROLES], "parenttype": "User"},
		fields=["parent", "role"],
	)
	roles = {}
	for row in rows:
		roles.setdefault(row.parent, set()).add(row.role)
	if not roles:
		return []
	users = frappe.get_all(
		"User",
		filters={"name": ["in", list(roles)]},
		fields=["name", "full_name", "email", "user_image", "enabled"],
		order_by="full_name asc",
	)
	for user in users:
		user.role = "Meeting Manager" if "Meeting Manager" in roles[user.name] else "Meeting User"
	return users


@frappe.whitelist()
def create_user(
	email: str,
	first_name: str,
	last_name: str | None = None,
	role: str = "Meeting User",
	send_welcome_email: bool = True,
) -> dict:
	"""Add someone to Meeting. An existing user just gets the role."""
	check_manager()
	email = (email or "").strip().lower()
	if not validate_email_address(email):
		frappe.throw(_("Enter a valid email address"))
	if not (first_name or "").strip():
		frappe.throw(_("First name is required"))
	check_role(role)

	if name := frappe.db.exists("User", {"email": email}):
		user = frappe.get_doc("User", name)
		created = False
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name.strip(),
				"last_name": (last_name or "").strip(),
				"user_type": "System User",
				"send_welcome_email": int(bool(send_welcome_email)),
			}
		)
		# Meeting managers may add people without full user-admin rights; the roles they
		# can hand out are limited to Meeting's own (see check_role).
		user.insert(ignore_permissions=True)
		created = True

	user.flags.ignore_permissions = True
	user.add_roles(*roles_for(role))
	return {"name": user.name, "created": created}


def check_manager():
	if not is_manager():
		frappe.throw(_("Only Meeting Managers can manage users"), frappe.PermissionError)


def check_role(role: str):
	if role not in MEETING_ROLES:
		frappe.throw(_("Role must be Meeting User or Meeting Manager"))
	if role == "Meeting Manager" and "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only a System Manager can add Meeting Managers"), frappe.PermissionError)


def roles_for(role: str) -> list[str]:
	# Managers also hold the user role, so every Meeting page treats them as members.
	return ["Meeting User", "Meeting Manager"] if role == "Meeting Manager" else ["Meeting User"]
