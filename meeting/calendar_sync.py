import re
from datetime import timedelta
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import add_days, get_datetime, get_system_timezone, now_datetime

from meeting.frappe_calendar import STATUS_TO_RSVP, FrappeCalendar, is_calendar_organizer

ISO_DURATION = re.compile(r"P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")


class CalendarChanges:
	"""Brings edits made in Frappe Calendar (title, time, participants) back into meetings."""

	@classmethod
	def pull_all(cls):
		"""Scheduled: check every upcoming meeting that has a calendar event."""
		meetings = frappe.get_all(
			"Meeting",
			filters={
				"calendar_event": ["is", "set"],
				"status": ["!=", "Cancelled"],
				"end": [">=", add_days(now_datetime(), -1)],
			},
			fields=["name", "calendar_event", "calendar_account"],
		)
		by_account = {}
		for m in meetings:
			by_account.setdefault(m.calendar_account, []).append(m)
		for account, rows in by_account.items():
			try:
				cls.pull_account(account, rows)
			except Exception:
				frappe.log_error(title=f"Meeting: calendar pull failed for account {account}")

	@classmethod
	def pull_account(cls, account: str, rows: list):
		get_user = frappe.get_attr("suite.mail.doctype.user_account.user_account.get_user_for_jmap_account")
		previous_user = frappe.session.user
		# Calendar reads are scoped to the account's owner.
		frappe.set_user(get_user(account))
		try:
			events = FrappeCalendar().call("get_calendar_events", account=account, ids=[r.calendar_event for r in rows])
			by_id = {e["id"]: e for e in events}
			for row in rows:
				cls(frappe.get_doc("Meeting", row.name)).apply(by_id.get(row.calendar_event))
		finally:
			frappe.set_user(previous_user)

	@classmethod
	def pull(cls, meeting):
		"""Refresh one meeting from its event, when the current user owns that calendar."""
		calendar = FrappeCalendar()
		if not meeting.calendar_event or meeting.calendar_account != calendar.get_account():
			return
		cls(meeting).apply(calendar.get_event(meeting.calendar_account, meeting.calendar_event))

	def __init__(self, meeting):
		self.meeting = meeting

	def apply(self, event: dict | None):
		if not event:
			self.unlink()
			return
		changed = self.apply_title(event) | self.apply_time(event) | self.apply_participants(event)
		if changed:
			# Saved without pushing back: the calendar already has these values.
			self.meeting.flags.from_calendar = True
			self.meeting.save(ignore_permissions=True)

	def unlink(self):
		"""The event was deleted in the calendar; the meeting stays, no longer linked."""
		self.meeting.db_set({"add_to_calendar": 0, "calendar_event": None, "calendar_account": None})

	def apply_title(self, event) -> bool:
		if event.get("title") and event["title"] != self.meeting.title:
			self.meeting.title = event["title"]
			return True
		return False

	def apply_time(self, event) -> bool:
		if not event.get("start") or not event.get("duration"):
			return False
		start = to_system_time(event["start"], event.get("time_zone"))
		end = start + parse_duration(event["duration"])
		if (start, end) == (get_datetime(self.meeting.start), get_datetime(self.meeting.end)):
			return False
		self.meeting.start, self.meeting.end = start, end
		return True

	def apply_participants(self, event) -> bool:
		wanted = {
			p["email"].lower(): p
			for p in event.get("participants", [])
			if p.get("email") and not is_calendar_organizer(p, event)
		}
		changed = False
		kept = []
		for row in self.meeting.attendees:
			email = (row.email or "").lower()
			if row.user == self.meeting.organizer:
				kept.append(row)
			elif email in wanted:
				rsvp = STATUS_TO_RSVP.get(wanted.pop(email).get("participation_status", "").lower())
				if rsvp and rsvp != row.rsvp:
					row.rsvp = rsvp
					changed = True
				kept.append(row)
			else:
				changed = True  # removed in the calendar
		self.meeting.attendees = kept
		for email, p in wanted.items():
			self.meeting.append(
				"attendees",
				{
					"email": email,
					"full_name": p.get("_name") if p.get("_name") != email else None,
					"rsvp": STATUS_TO_RSVP.get(p.get("participation_status", "").lower(), "Pending"),
				},
			)
			changed = True
		return changed


def pull_calendar_changes():
	"""Scheduled every few minutes."""
	CalendarChanges.pull_all()


def to_system_time(local: str, time_zone: str | None):
	"""An event's local start in its own zone, as a naive datetime in the site's zone."""
	system = ZoneInfo(get_system_timezone())
	start = get_datetime(local.rstrip("Z")).replace(tzinfo=ZoneInfo(time_zone) if time_zone else system)
	return start.astimezone(system).replace(tzinfo=None)


def parse_duration(value: str) -> timedelta:
	match = ISO_DURATION.match(value or "")
	if not match:
		return timedelta(hours=1)
	weeks, days, hours, minutes, seconds = (int(g or 0) for g in match.groups())
	return timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
