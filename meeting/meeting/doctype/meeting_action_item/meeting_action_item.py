# Copyright (c) 2026, Mohsin Akhtar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class MeetingActionItem(Document):
	def validate(self):
		self.set_completed_on()

	def after_insert(self):
		self.notify_assignee()

	def set_completed_on(self):
		if self.status == "Done" and not self.completed_on:
			self.completed_on = today()
		elif self.status != "Done":
			self.completed_on = None

	def notify_assignee(self):
		if not self.assigned_to or self.assigned_to == frappe.session.user:
			return
		frappe.get_doc(
			{
				"doctype": "Notification Log",
				"for_user": self.assigned_to,
				"from_user": frappe.session.user,
				"type": "Assignment",
				"document_type": self.doctype,
				"document_name": self.name,
				"subject": frappe._("New action item: {0}").format(self.title),
			}
		).insert(ignore_permissions=True)
