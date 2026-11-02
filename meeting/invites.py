from datetime import timezone
from zoneinfo import ZoneInfo

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, get_system_timezone, get_url, now_datetime

from meeting.recurrence import repeat_message, to_ics_rrule


class MeetingInvite:
	"""Emails a meeting invite (with an .ics calendar file) to attendees."""

	def __init__(self, meeting):
		self.meeting = meeting

	def send(self, only_pending: bool = False) -> int:
		recipients = [
			row.email
			for row in self.meeting.attendees
			if row.email
			and row.user != self.meeting.organizer
			and not (only_pending and row.rsvp != "Pending")
		]
		if not recipients:
			return 0
		frappe.sendmail(
			recipients=recipients,
			subject=_("Invitation: {0}").format(self.meeting.title),
			message=self.message(),
			attachments=[{"fname": "invite.ics", "fcontent": self.ics()}],
			reference_doctype="Meeting",
			reference_name=self.meeting.name,
			now=frappe.flags.in_test,
		)
		self.meeting.db_set("invites_sent_on", now_datetime())
		return len(recipients)

	def send_reminder(self):
		recipients = [row.email for row in self.meeting.attendees if row.email and row.rsvp != "Declined"]
		if not recipients:
			return
		frappe.sendmail(
			recipients=recipients,
			subject=_("Reminder: {0} starts soon").format(self.meeting.title),
			message=self.message(),
			reference_doctype="Meeting",
			reference_name=self.meeting.name,
		)

	def message(self) -> str:
		m = self.meeting
		start = frappe.utils.format_datetime(m.start, "EEEE, d MMM yyyy h:mm a")
		lines = [
			f"<p><b>{frappe.utils.escape_html(m.title)}</b></p>",
			f"<p>{_('When')}: {start} ({get_system_timezone()})</p>",
		]
		if rule := self.repeat_rule():
			lines.append(f"<p>{_('Repeats')}: {repeat_message(rule)}</p>")
		if m.location:
			lines.append(f"<p>{_('Where')}: {frappe.utils.escape_html(m.location)}</p>")
		if m.video_link:
			lines.append(f'<p>{_("Join")}: <a href="{m.video_link}">{m.video_link}</a></p>')
		if m.agenda:
			items = "".join(f"<li>{frappe.utils.escape_html(a.topic)}</li>" for a in m.agenda)
			lines.append(f"<p>{_('Agenda')}:</p><ul>{items}</ul>")
		lines.append(f'<p><a href="{self.url()}">{_("View and RSVP")}</a></p>')
		return "\n".join(lines)

	def repeat_rule(self) -> dict | None:
		"""Only the first meeting's invite describes the series."""
		m = self.meeting
		return frappe.parse_json(m.repeat_rule) if m.repeat and not m.repeat_of and m.repeat_rule else None

	def url(self) -> str:
		return get_url(f"/meeting/meetings/{self.meeting.name}")

	def ics(self) -> str:
		m = self.meeting
		location = m.video_link or m.location or ""
		description = (m.description or "") + f"\\n\\n{self.url()}"
		lines = [
			"BEGIN:VCALENDAR",
			"VERSION:2.0",
			"PRODID:-//Frappe//Meeting//EN",
			"METHOD:REQUEST",
			"BEGIN:VEVENT",
			f"UID:{m.name}@{frappe.local.site}",
			f"DTSTAMP:{to_ics_utc(now_datetime())}",
			f"DTSTART:{to_ics_utc(m.start)}",
			f"DTEND:{to_ics_utc(m.end)}",
			*([f"RRULE:{to_ics_rrule(rule, to_ics_utc)}"] if (rule := self.repeat_rule()) else []),
			f"SUMMARY:{ics_escape(m.title)}",
			f"LOCATION:{ics_escape(location)}",
			f"DESCRIPTION:{ics_escape(description)}",
			f"ORGANIZER:mailto:{frappe.db.get_value('User', m.organizer, 'email') or m.organizer}",
		]
		lines += [f"ATTENDEE;RSVP=TRUE:mailto:{row.email}" for row in m.attendees if row.email]
		lines += ["END:VEVENT", "END:VCALENDAR"]
		return "\r\n".join(lines)


def send_upcoming_reminders():
	"""Scheduled: remind attendees of meetings starting within the next 30 minutes."""
	now = now_datetime()
	meetings = frappe.get_all(
		"Meeting",
		filters={
			"status": "Scheduled",
			"reminder_sent": 0,
			"start": ["between", [now, add_to_date(now, minutes=30)]],
		},
		pluck="name",
	)
	for name in meetings:
		meeting = frappe.get_doc("Meeting", name)
		MeetingInvite(meeting).send_reminder()
		meeting.db_set("reminder_sent", 1)


def to_ics_utc(value) -> str:
	local = get_datetime(value).replace(tzinfo=ZoneInfo(get_system_timezone()))
	return local.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ics_escape(text: str) -> str:
	return (text or "").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
