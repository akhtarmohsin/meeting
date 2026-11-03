import frappe
from frappe import _
from frappe.utils import get_datetime, get_system_timezone, get_url, time_diff_in_seconds

# Meeting RSVP <-> JMAP participationStatus.
RSVP_TO_STATUS = {
	"Accepted": "accepted",
	"Declined": "declined",
	"Tentative": "tentative",
	"Pending": "needs-action",
}
STATUS_TO_RSVP = {status: rsvp for rsvp, status in RSVP_TO_STATUS.items()}


class FrappeCalendar:
	"""Keeps an event in the user's Frappe Calendar (part of Frappe Suite) in step with a meeting."""

	EVENT_API = "suite.calendar.doctype.calendar_event.calendar_event"

	def __init__(self, user: str | None = None):
		self.user = user or frappe.session.user

	def is_available(self) -> bool:
		return bool(self.get_account())

	def get_account(self) -> str | None:
		"""The user's personal calendar account, or None when Suite or their mail account is missing."""
		if "suite" not in frappe.get_installed_apps():
			return None
		can_use_mail = frappe.get_attr("suite.mail.utils.user.can_use_mail")
		if not can_use_mail(self.user):
			return None
		get_account = frappe.get_attr(
			"suite.mail.doctype.user_account.user_account.get_user_personal_jmap_account"
		)
		return get_account(self.user)

	def sync(self, meeting):
		if meeting.add_to_calendar:
			self.save_event(meeting)
		elif meeting.calendar_event:
			self.delete_event(meeting)

	def save_event(self, meeting):
		if meeting.calendar_event and meeting.calendar_account != self.get_account():
			# The event lives in someone else's calendar; only they can change it.
			return
		account = self.get_account()
		if not account:
			frappe.throw(
				_("Frappe Calendar is not set up for you. Connect your mail account in Frappe Suite first.")
			)
		current = self.get_event(account, meeting.calendar_event) if meeting.calendar_event else None
		if current:
			# Suite replaces the whole event on update, so carry over what we don't own.
			self.call(
				"update_calendar_event",
				account=account,
				id=meeting.calendar_event,
				uid=current["uid"],
				organizer=current.get("organizer"),
				calendar_ids=[c["calendar_id"] for c in current.get("calendars", [])] or None,
				**self.event(meeting, current),
			)
		else:
			# New, or deleted from the calendar since: create it (again).
			event_id = self.call("add_calendar_event", account=account, **self.event(meeting))
			meeting.db_set({"calendar_event": event_id, "calendar_account": account})

	def get_event(self, account: str, event_id: str) -> dict | None:
		events = self.call("get_calendar_events", account=account, ids=[event_id])
		return events[0] if events else None

	def delete_event(self, meeting):
		if meeting.calendar_account != self.get_account():
			return
		self.call("delete_calendar_events", account=meeting.calendar_account, ids=[meeting.calendar_event])
		meeting.db_set({"calendar_event": None, "calendar_account": None})

	def call(self, method: str, **kwargs):
		return frappe.get_attr(f"{self.EVENT_API}.{method}")(**kwargs)

	def event(self, meeting, current: dict | None = None) -> dict:
		return {
			"title": meeting.title,
			"start": get_datetime(meeting.start).strftime("%Y-%m-%dT%H:%M:%S"),
			"duration": iso_duration(time_diff_in_seconds(meeting.end, meeting.start)),
			"time_zone": get_system_timezone(),
			"status": "Cancelled" if meeting.status == "Cancelled" else "Confirmed",
			"description": self.description(meeting),
			"locations": [{"name": meeting.location}] if meeting.location else None,
			"participants": self.participants(meeting, current),
		}

	def participants(self, meeting, current: dict | None) -> list[dict] | None:
		"""Attendees as calendar participants. No invites are asked for: the meeting app sends its own."""
		previous = {p["email"].lower(): p for p in (current or {}).get("participants", []) if p.get("email")}
		# Calendar's own organizer entry is kept as it is.
		rows = [as_input(p) for p in previous.values() if is_calendar_organizer(p, current)]
		for row in meeting.attendees:
			if row.user == meeting.organizer or not row.email:
				continue
			email = row.email.lower()
			rows.append(
				{
					"uid": previous.get(email, {}).get("uid"),
					"email": email,
					"name": row.full_name or email,
					"roles": {"attendee": True},
					"participation_status": RSVP_TO_STATUS.get(row.rsvp, "needs-action"),
					"expect_reply": False,
				}
			)
		return rows or None

	def description(self, meeting) -> str:
		parts = [meeting.description or ""]
		if meeting.video_link:
			parts.append(_("Join: {0}").format(meeting.video_link))
		parts.append(_("Agenda and minutes: {0}").format(get_url(f"/meeting/meetings/{meeting.name}")))
		return "\n\n".join(p for p in parts if p).strip()


def is_calendar_organizer(participant: dict, event: dict | None) -> bool:
	roles = participant.get("roles") or {}
	return bool(roles.get("owner") or roles.get("chair")) or (
		participant.get("email", "").lower() == (event or {}).get("organizer", "").lower()
	)


def as_input(participant: dict) -> dict:
	"""A participant as Suite returns it, in the shape Suite accepts back."""
	return {
		"uid": participant.get("uid"),
		"email": participant["email"],
		"name": participant.get("_name") or participant["email"],
		"roles": participant.get("roles") or None,
		"participation_status": (participant.get("participation_status") or "").lower() or None,
		"expect_reply": bool(participant.get("expect_reply")),
		"kind": participant.get("kind") or None,
	}


def iso_duration(seconds: float) -> str:
	minutes = max(int(seconds // 60), 1)
	hours, minutes = divmod(minutes, 60)
	return "PT" + (f"{hours}H" if hours else "") + (f"{minutes}M" if minutes else "")
