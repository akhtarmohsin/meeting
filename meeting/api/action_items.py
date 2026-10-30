import frappe
from frappe import _

ACTION_ITEM_FIELDS = [
	"name",
	"title",
	"status",
	"priority",
	"assigned_to",
	"due_date",
	"meeting",
	"description",
	"completed_on",
]
EDITABLE_FIELDS = {"title", "status", "priority", "assigned_to", "due_date", "meeting", "description"}
STATUS_OPTIONS = ("Open", "In Progress", "Done", "Cancelled")


@frappe.whitelist()
def get_action_items(scope: str = "mine", status: str | None = None) -> list[dict]:
	filters = {}
	if scope == "mine":
		filters["assigned_to"] = frappe.session.user
	if status == "pending":
		filters["status"] = ["in", ["Open", "In Progress"]]
	elif status:
		filters["status"] = status
	items = frappe.get_list(
		"Meeting Action Item",
		fields=ACTION_ITEM_FIELDS,
		filters=filters,
		order_by="creation desc",
		limit=500,
	)
	# Soonest due first, undated items last.
	items.sort(key=lambda i: (i.due_date is None, i.due_date or ""))
	attach_meeting_titles(items)
	return items


@frappe.whitelist()
def save_action_item(data: dict, name: str | None = None) -> str:
	values = {k: v for k, v in data.items() if k in EDITABLE_FIELDS}
	doc = frappe.get_doc("Meeting Action Item", name) if name else frappe.new_doc("Meeting Action Item")
	doc.update(values)
	doc.save()
	return doc.name


@frappe.whitelist()
def set_status(name: str, status: str) -> str:
	if status not in STATUS_OPTIONS:
		frappe.throw(_("Invalid status"))
	doc = frappe.get_doc("Meeting Action Item", name)
	doc.status = status
	doc.save()
	return doc.status


@frappe.whitelist()
def delete_action_item(name: str) -> None:
	frappe.delete_doc("Meeting Action Item", name)


def attach_meeting_titles(items: list[dict]) -> None:
	names = list({i.meeting for i in items if i.meeting})
	if not names:
		return
	titles = dict(frappe.get_all("Meeting", filters={"name": ["in", names]}, fields=["name", "title"], as_list=True))
	for item in items:
		item.meeting_title = titles.get(item.meeting)
