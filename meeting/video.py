import frappe
from frappe import _
from frappe.utils import get_url

FRAPPE_MEET = "Frappe Meet"


class FrappeMeet:
	"""Creates video rooms in Frappe Meet, which ships with the Frappe Suite app."""

	@staticmethod
	def is_available() -> bool:
		return "suite" in frappe.get_installed_apps()

	def create_room(self, title: str | None = None) -> dict:
		self.check_access()
		# Suite's own endpoint keeps its room defaults, permissions and rate limits in force.
		create = frappe.get_attr("suite.meet.api.meeting.create")
		room = create(meeting_type="open", title=title)
		return {
			"video_provider": FRAPPE_MEET,
			"meet_room": room,
			"video_link": get_url(f"/meet/{room}"),
		}

	def check_access(self):
		if not self.is_available():
			frappe.throw(_("Frappe Meet is not available. Install the Frappe Suite app on this site to use it."))
		if not frappe.has_permission("Meet Room", "create"):
			frappe.throw(
				_("You need the Suite User role to create Frappe Meet rooms."), frappe.PermissionError
			)
