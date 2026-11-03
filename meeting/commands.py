import click
from frappe.commands import get_site, pass_context


@click.command("meeting-demo")
@click.option("--reset", is_flag=True, help="Delete all meetings and action items first.")
@click.option("--yes", is_flag=True, help="Don't ask before deleting.")
@click.option("--url", help="Address of the site, for Frappe Meet links (e.g. http://suite.localhost:8124).")
@pass_context
def meeting_demo(context, reset=False, yes=False, url=None):
	"""Fill the site with demo meetings that show every Meeting feature. Sends no email."""
	import frappe

	from meeting.demo import MeetingDemo

	site = get_site(context)
	if reset and not yes:
		click.confirm(f"Delete every meeting and action item on {site}?", abort=True)

	frappe.init(site)
	frappe.connect()
	try:
		frappe.set_user("Administrator")
		summary = MeetingDemo(site_url=url).run(reset=reset)
		frappe.db.commit()
		click.echo(summary)
	finally:
		frappe.destroy()


commands = [meeting_demo]
