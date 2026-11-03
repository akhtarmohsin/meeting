# Copyright (c) 2026, Mohsin Akhtar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime

from meeting.frappe_calendar import FrappeCalendar
from meeting.recurrence import MeetingSeries, parse_rule
from meeting.video import FRAPPE_MEET

# Changes to these fields are copied to the meeting's calendar event.
CALENDAR_FIELDS = (
	"add_to_calendar",
	"title",
	"start",
	"end",
	"status",
	"description",
	"location",
	"video_link",
)


class Meeting(Document):
	def validate(self):
		self.organizer = self.organizer or frappe.session.user
		self.validate_schedule()
		self.validate_repeat()
		self.clear_stale_meet_room()
		self.set_attendee_details()
		self.add_organizer_as_attendee()
		self.remove_duplicate_attendees()

	def after_insert(self):
		if self.is_series_root():
			MeetingSeries(self).create_upcoming()

	def on_update(self):
		if self.has_value_changed("start"):
			# Rescheduled meetings need a fresh reminder.
			self.db_set("reminder_sent", 0)
		if self.calendar_needs_sync():
			FrappeCalendar().sync(self)

	def on_trash(self):
		if self.is_series_root():
			MeetingSeries(self).detach_occurrences()
		if self.calendar_event:
			self.add_to_calendar = 0
			FrappeCalendar().sync(self)

	def calendar_needs_sync(self) -> bool:
		if self.flags.from_calendar:
			return False
		if not (self.add_to_calendar or self.calendar_event):
			return False
		if not self.calendar_event:
			return True
		return any(self.has_value_changed(field) for field in CALENDAR_FIELDS)

	def is_series_root(self) -> bool:
		return bool(self.repeat and not self.repeat_of)

	def validate_repeat(self):
		if self.repeat_of:
			# Occurrences follow the first meeting's rule; they don't carry one.
			self.repeat, self.repeat_rule = 0, None
		elif self.repeat:
			parse_rule(self.repeat_rule)
		else:
			self.repeat_rule = None

	def validate_schedule(self):
		if get_datetime(self.end) <= get_datetime(self.start):
			frappe.throw(_("End time must be after start time"))

	def clear_stale_meet_room(self):
		if self.video_provider != FRAPPE_MEET or self.meeting_type == "In Person":
			self.meet_room = None

	def set_attendee_details(self):
		for row in self.attendees:
			if row.user:
				row.email = frappe.db.get_value("User", row.user, "email") or row.email
			if not row.user and row.email:
				row.user = frappe.db.get_value("User", {"email": row.email})
			if row.user and not row.full_name:
				row.full_name = frappe.utils.get_fullname(row.user)

	def add_organizer_as_attendee(self):
		if self.get_attendee(self.organizer):
			return
		self.append(
			"attendees",
			{
				"user": self.organizer,
				"email": frappe.db.get_value("User", self.organizer, "email") or self.organizer,
				"full_name": frappe.utils.get_fullname(self.organizer),
				"rsvp": "Accepted",
			},
		)

	def remove_duplicate_attendees(self):
		seen, unique = set(), []
		for row in self.attendees:
			key = (row.email or "").lower()
			if key in seen:
				continue
			seen.add(key)
			unique.append(row)
		self.attendees = unique
		for idx, row in enumerate(self.attendees, 1):
			row.idx = idx

	def get_attendee(self, user: str):
		return next((row for row in self.attendees if user in (row.user, row.email)), None)

	def is_organizer(self, user: str | None = None) -> bool:
		return (user or frappe.session.user) == self.organizer

	def set_rsvp(self, user: str, response: str):
		attendee = self.get_attendee(user)
		if not attendee:
			frappe.throw(_("You are not invited to this meeting"), frappe.PermissionError)
		attendee.rsvp = response
		self.flags.ignore_permissions = True
		self.save()
