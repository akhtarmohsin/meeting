// Copyright (c) 2026, Mohsin Akhtar and contributors
// For license information, please see license.txt

frappe.ui.form.on("Meeting", {
	refresh(frm) {
		if (frm.doc.video_link) {
			frm.add_custom_button(__("Join Meeting"), () =>
				window.open(frm.doc.video_link, "_blank")
			);
		}
	},

	video_provider(frm) {
		// A Meet room only belongs to the Frappe Meet provider.
		if (frm.doc.video_provider !== "Frappe Meet" && frm.doc.meet_room) {
			frm.set_value("meet_room", "");
		}
	},

	generate_meet_link(frm) {
		const generate = () =>
			frappe
				.call({
					method: "meeting.api.meetings.create_frappe_meet_link",
					args: { title: frm.doc.title },
					freeze: true,
					freeze_message: __("Creating Frappe Meet room..."),
				})
				.then(({ message }) => {
					frm.set_value(message);
					frappe.show_alert({
						message: __("Frappe Meet link created"),
						indicator: "green",
					});
				});

		if (frm.doc.video_link) {
			frappe.confirm(
				__("Replace the current video link with a new Frappe Meet link?"),
				generate
			);
		} else {
			generate();
		}
	},
});
