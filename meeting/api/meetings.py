import frappe
from frappe import _
from frappe.utils import add_days, getdate, now_datetime, today

from meeting.invites import MeetingInvite

MEETING_LIST_FIELDS = [
	"name",
	"title",
	"status",
	"start",
	"end",
	"organizer",
	"meeting_type",
	"location",
	"video_provider",
	"video_link",
]
RSVP_OPTIONS = ("Accepted", "Declined", "Tentative")
EDITABLE_FIELDS = {
	"title",
	"status",
	"organizer",
	"meeting_type",
	"start",
	"end",
	"location",
	"video_provider",
	"video_link",
	"description",
	"attendees",
	"agenda",
	"minutes",
	"decisions",
}


@frappe.whitelist()
def get_meetings(view: str = "upcoming", search: str | None = None, limit: int = 100) -> list[dict]:
	filters = {"upcoming": [["end", ">=", now_datetime()], ["status", "!=", "Cancelled"]],
		"past": [["end", "<", now_datetime()]], "all": []}[view]
	if search:
		filters.append(["title", "like", f"%{search}%"])
	meetings = frappe.get_list(
		"Meeting",
		fields=MEETING_LIST_FIELDS,
		filters=filters,
		order_by="start asc" if view == "upcoming" else "start desc",
		limit=limit,
	)
	attach_attendees(meetings)
	return meetings


@frappe.whitelist()
def get_meeting(name: str) -> dict:
	doc = frappe.get_doc("Meeting", name)
	doc.check_permission("read")
	me = doc.get_attendee(frappe.session.user)
	return {
		"doc": doc.as_dict(),
		"can_edit": doc.has_permission("write"),
		"my_rsvp": me.rsvp if me else None,
		"action_items": frappe.get_list(
			"Meeting Action Item",
			filters={"meeting": name},
			fields=["name", "title", "status", "priority", "assigned_to", "due_date"],
			order_by="creation asc",
		),
	}


@frappe.whitelist()
def save_meeting(data: dict, name: str | None = None) -> str:
	values = {k: v for k, v in data.items() if k in EDITABLE_FIELDS}
	doc = frappe.get_doc("Meeting", name) if name else frappe.new_doc("Meeting")
	doc.update(values)
	doc.save()
	return doc.name


@frappe.whitelist()
def rsvp(name: str, response: str) -> str:
	if response not in RSVP_OPTIONS:
		frappe.throw(_("Invalid response"))
	doc = frappe.get_doc("Meeting", name)
	doc.check_permission("read")
	doc.set_rsvp(frappe.session.user, response)
	return response


@frappe.whitelist()
def send_invites(name: str, only_pending: bool = False) -> int:
	doc = frappe.get_doc("Meeting", name)
	doc.check_permission("write")
	return MeetingInvite(doc).send(only_pending=only_pending)


@frappe.whitelist()
def delete_meeting(name: str) -> None:
	frappe.delete_doc("Meeting", name)


@frappe.whitelist()
def get_dashboard() -> dict:
	user = frappe.session.user
	start_of_day = getdate(today())
	todays = get_meetings_between(start_of_day, add_days(start_of_day, 1))
	return {
		"today": todays,
		"upcoming": get_meetings("upcoming", limit=6),
		"pending_rsvp": pending_rsvp_count(user),
		"open_action_items": frappe.db.count(
			"Meeting Action Item", {"assigned_to": user, "status": ["in", ["Open", "In Progress"]]}
		),
		"overdue_action_items": frappe.db.count(
			"Meeting Action Item",
			{"assigned_to": user, "status": ["in", ["Open", "In Progress"]], "due_date": ["<", today()]},
		),
	}


@frappe.whitelist()
def search_users(txt: str = "") -> list[dict]:
	return frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Guest", "Administrator"]]},
		or_filters={"full_name": ["like", f"%{txt}%"], "email": ["like", f"%{txt}%"]},
		fields=["name", "full_name", "email", "user_image"],
		limit=20,
		order_by="full_name asc",
	)


def get_meetings_between(start, end) -> list[dict]:
	meetings = frappe.get_list(
		"Meeting",
		fields=MEETING_LIST_FIELDS,
		filters=[["start", ">=", start], ["start", "<", end], ["status", "!=", "Cancelled"]],
		order_by="start asc",
	)
	attach_attendees(meetings)
	return meetings


def pending_rsvp_count(user: str) -> int:
	Meeting = frappe.qb.DocType("Meeting")
	Attendee = frappe.qb.DocType("Meeting Attendee")
	rows = (
		frappe.qb.from_(Attendee)
		.join(Meeting)
		.on(Meeting.name == Attendee.parent)
		.select(Attendee.name)
		.where(
			(Attendee.parenttype == "Meeting")
			& (Attendee.user == user)
			& (Attendee.rsvp == "Pending")
			& (Meeting.status == "Scheduled")
			& (Meeting.start >= now_datetime())
		)
	).run()
	return len(rows)


def attach_attendees(meetings: list[dict]) -> None:
	if not meetings:
		return
	rows = frappe.get_all(
		"Meeting Attendee",
		filters={"parenttype": "Meeting", "parent": ["in", [m.name for m in meetings]]},
		fields=["parent", "user", "email", "full_name", "rsvp"],
		order_by="idx asc",
	)
	by_meeting = {}
	for row in rows:
		by_meeting.setdefault(row.parent, []).append(row)
	for m in meetings:
		m.attendees = by_meeting.get(m.name, [])
