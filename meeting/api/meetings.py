import frappe
from frappe import _
from frappe.utils import add_days, getdate, now_datetime, strip_html, today

from meeting.calendar_sync import CalendarChanges
from meeting.invites import MeetingInvite
from meeting.recurrence import repeat_message
from meeting.video import FrappeMeet

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
	"meet_room",
	"add_to_calendar",
	"repeat",
	"repeat_rule",
	"description",
	"attendees",
	"agenda",
	"minutes",
	"decisions",
}


@frappe.whitelist()
def get_meetings(view: str = "upcoming", search: str | None = None, limit: int = 100) -> list[dict]:
	if view in ("minutes_pending", "awaiting_reply"):
		find = meetings_needing_minutes if view == "minutes_pending" else meetings_awaiting_reply
		meetings = find(frappe.session.user, search)
		attach_attendees(meetings)
		return meetings
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
	refresh_from_calendar(doc)
	me = doc.get_attendee(frappe.session.user)
	return {
		"doc": doc.as_dict(),
		"can_edit": doc.has_permission("write"),
		"my_rsvp": me.rsvp if me else None,
		"series": get_series(doc),
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
	if name:
		# A series is set up when the first meeting is created and can't be reshaped after.
		values.pop("repeat", None)
		values.pop("repeat_rule", None)
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
def create_frappe_meet_link(title: str | None = None) -> dict:
	"""Create a Frappe Meet room; the caller stores the returned fields on the meeting."""
	return FrappeMeet().create_room(title)


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
		"pending_rsvp": len(meetings_awaiting_reply(user)),
		"minutes_pending": len(meetings_needing_minutes(user)),
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


@frappe.whitelist()
def search_user_groups(txt: str = "") -> list[dict]:
	"""Frappe User Groups for the attendee picker, with how many people each holds."""
	groups = frappe.get_all(
		"User Group", filters={"name": ["like", f"%{txt}%"]}, pluck="name", limit=10, order_by="name asc"
	)
	counts = dict(
		frappe.get_all(
			"User Group Member",
			filters={"parenttype": "User Group", "parent": ["in", groups or [""]]},
			fields=["parent", {"COUNT": "*"}],
			group_by="parent",
			as_list=True,
		)
	)
	return [{"name": g, "member_count": counts.get(g, 0)} for g in groups]


@frappe.whitelist()
def get_user_group_members(group: str) -> list[dict]:
	"""The enabled members of a User Group, ready to add as attendees."""
	users = frappe.get_all(
		"User Group Member", filters={"parenttype": "User Group", "parent": group}, pluck="user"
	)
	return frappe.get_all(
		"User",
		filters={"name": ["in", users or [""]], "enabled": 1},
		fields=["name", "full_name", "email"],
		order_by="full_name asc",
	)


@frappe.whitelist()
def get_meeting_users() -> list[dict]:
	"""Everyone who can use Meeting, for the attendee picker's "Add all"."""
	names = frappe.get_all(
		"Has Role",
		filters={"role": ["in", ["Meeting User", "Meeting Manager"]], "parenttype": "User"},
		pluck="parent",
		distinct=True,
	)
	return frappe.get_all(
		"User",
		filters={"name": ["in", names or [""]], "enabled": 1},
		fields=["name", "full_name", "email"],
		order_by="full_name asc",
	)


def refresh_from_calendar(doc) -> None:
	"""Show edits made in Frappe Calendar straight away; the scheduled pull catches the rest."""
	if not doc.calendar_event:
		return
	try:
		CalendarChanges.pull(doc)
	except Exception:
		# A calendar that can't be reached shouldn't stop the meeting from opening.
		frappe.log_error(title=f"Meeting: calendar refresh failed for {doc.name}")
	doc.reload()


def get_series(doc) -> dict | None:
	root_name = doc.repeat_of or (doc.name if doc.repeat else None)
	if not root_name:
		return None
	rule = frappe.parse_json(frappe.db.get_value("Meeting", root_name, "repeat_rule") or "{}")
	starts = [root_name, *frappe.get_all("Meeting", filters={"repeat_of": root_name}, order_by="start asc", pluck="name")]
	return {
		"root": root_name,
		"rule": rule,
		"message": repeat_message(rule) if rule else "",
		"index": starts.index(doc.name) + 1,
		"total": len(starts),
	}


def get_meetings_between(start, end) -> list[dict]:
	meetings = frappe.get_list(
		"Meeting",
		fields=MEETING_LIST_FIELDS,
		filters=[["start", ">=", start], ["start", "<", end], ["status", "!=", "Cancelled"]],
		order_by="start asc",
	)
	attach_attendees(meetings)
	return meetings


def meetings_needing_minutes(user: str, search: str | None = None) -> list[dict]:
	"""Meetings the user organised that have ended, weren't cancelled, and still have no minutes."""
	filters = [["organizer", "=", user], ["end", "<", now_datetime()], ["status", "!=", "Cancelled"]]
	if search:
		filters.append(["title", "like", f"%{search}%"])
	meetings = frappe.get_list(
		"Meeting", fields=[*MEETING_LIST_FIELDS, "minutes"], filters=filters, order_by="start desc", limit=200
	)
	# An editor opened and left blank saves "<p></p>", which still means no minutes.
	pending = [m for m in meetings if not strip_html(m.minutes or "").strip()]
	for m in pending:
		del m["minutes"]
	return pending


def meetings_awaiting_reply(user: str, search: str | None = None) -> list[dict]:
	"""Scheduled meetings still to come that the user was invited to and hasn't answered."""
	invited = frappe.get_all(
		"Meeting Attendee",
		filters={"parenttype": "Meeting", "user": user, "rsvp": "Pending"},
		pluck="parent",
	)
	filters = [["name", "in", invited or [""]], ["status", "=", "Scheduled"], ["start", ">=", now_datetime()]]
	if search:
		filters.append(["title", "like", f"%{search}%"])
	return frappe.get_list(
		"Meeting", fields=MEETING_LIST_FIELDS, filters=filters, order_by="start asc", limit=200
	)


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
