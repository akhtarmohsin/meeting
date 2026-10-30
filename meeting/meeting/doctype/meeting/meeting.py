# Copyright (c) 2026, Mohsin Akhtar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime


class Meeting(Document):
	def validate(self):
		self.organizer = self.organizer or frappe.session.user
		self.validate_schedule()
		self.set_attendee_details()
		self.add_organizer_as_attendee()
		self.remove_duplicate_attendees()

	def on_update(self):
		if self.has_value_changed("start"):
			# Rescheduled meetings need a fresh reminder.
			self.db_set("reminder_sent", 0)

	def validate_schedule(self):
		if get_datetime(self.end) <= get_datetime(self.start):
			frappe.throw(_("End time must be after start time"))

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
