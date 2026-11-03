import frappe
from frappe.tests import IntegrationTestCase

from meeting.api import meetings as meetings_api
from meeting.api import users as api

MANAGER = "users-manager@example.com"
MEMBER = "users-member@example.com"


class TestMeetingUsers(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_user(MANAGER, "Meeting Manager", "Meeting User")
		make_user(MEMBER, "Meeting User")

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_manager_creates_user_with_meeting_role(self):
		result = api.create_user("new.person@example.com", "New", "Person", send_welcome_email=False)
		self.assertTrue(result["created"])
		self.assertIn("Meeting User", frappe.get_roles("new.person@example.com"))
		listed = {u.email: u.role for u in api.get_users()}
		self.assertEqual(listed["new.person@example.com"], "Meeting User")

	def test_existing_user_gets_role_instead_of_duplicate(self):
		make_user("existing.person@example.com")
		result = api.create_user("Existing.Person@example.com", "Ignored", send_welcome_email=False)
		self.assertFalse(result["created"])
		self.assertIn("Meeting User", frappe.get_roles("existing.person@example.com"))
		self.assertEqual(frappe.db.count("User", {"email": "existing.person@example.com"}), 1)

	def test_member_cannot_manage_users(self):
		frappe.set_user(MEMBER)
		self.assertRaises(frappe.PermissionError, api.create_user, "x@example.com", "X")
		self.assertRaises(frappe.PermissionError, api.get_users)

	def test_meeting_manager_cannot_create_managers(self):
		frappe.set_user(MANAGER)
		self.assertRaises(
			frappe.PermissionError, api.create_user, "boss@example.com", "Boss", role="Meeting Manager"
		)
		result = api.create_user("helper@example.com", "Helper", send_welcome_email=False)
		self.assertTrue(result["created"])

	def test_meeting_users_lists_only_enabled_meeting_people(self):
		make_user("no.role@example.com")
		make_user("disabled.member@example.com", "Meeting User")
		frappe.db.set_value("User", "disabled.member@example.com", "enabled", 0)

		frappe.set_user(MEMBER)  # any Meeting user may ask
		emails = {u.email for u in meetings_api.get_meeting_users()}
		self.assertIn(MEMBER, emails)
		self.assertIn(MANAGER, emails)
		self.assertNotIn("no.role@example.com", emails)
		self.assertNotIn("disabled.member@example.com", emails)

	def test_user_group_search_and_members(self):
		make_user("group.off@example.com")
		frappe.db.set_value("User", "group.off@example.com", "enabled", 0)
		group = frappe.get_doc(
			{
				"doctype": "User Group",
				"__newname": "Meeting Test Group",
				"user_group_members": [
					{"user": MEMBER},
					{"user": MANAGER},
					{"user": "group.off@example.com"},
				],
			}
		).insert(ignore_permissions=True)

		frappe.set_user(MEMBER)
		found = {g["name"]: g["member_count"] for g in meetings_api.search_user_groups("Test Gro")}
		self.assertEqual(found.get(group.name), 3)
		emails = {u.email for u in meetings_api.get_user_group_members(group.name)}
		self.assertEqual(emails, {MEMBER, MANAGER})  # the disabled member is left out

	def test_rejects_bad_role_and_email(self):
		self.assertRaises(
			frappe.ValidationError, api.create_user, "ok@example.com", "Ok", role="System Manager"
		)
		self.assertRaises(frappe.ValidationError, api.create_user, "not-an-email", "Bad")


def make_user(email: str, *roles: str):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	if roles:
		frappe.get_doc("User", email).add_roles(*roles)
