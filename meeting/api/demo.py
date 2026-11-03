import frappe

from meeting.demo import MeetingDemo


@frappe.whitelist(methods=["POST"])
def load_demo(reset: bool = False) -> str:
	"""Fill the site with demo meetings built around the current user. Sends no email."""
	frappe.only_for("System Manager")
	me = frappe.session.user
	# Demo people, groups and other people's meetings need more than the user's own rights.
	frappe.set_user("Administrator")
	try:
		return MeetingDemo(me=me).run(reset=frappe.utils.sbool(reset))
	finally:
		frappe.set_user(me)
