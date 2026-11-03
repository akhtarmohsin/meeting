<template>
	<SettingsHeader title="Preferences" />
	<!-- Inputs fill their container in frappe-ui 1.0, so each width lives on a wrapper. -->
	<SettingsBody>
		<div class="flex flex-col gap-6 pt-6">
			<SettingsRow title="Language" description="The language that the interface is shown in">
				<div class="w-56">
					<FormControl
						type="combobox"
						placeholder="Select language"
						:model-value="user.data?.language || siteLanguage.data"
						:options="languages.data || []"
						@update:model-value="(value) => save('language', value)"
					/>
				</div>
			</SettingsRow>
			<SettingsRow title="Time zone" description="Meeting times are shown in this time zone">
				<div class="w-56">
					<FormControl
						type="combobox"
						placeholder="Select time zone"
						:model-value="user.data?.time_zone"
						:options="timeZoneOptions"
						@update:model-value="(value) => save('time_zone', value)"
					/>
				</div>
			</SettingsRow>
			<SettingsRow title="Theme" description="Choose a light or dark appearance, or follow your device">
				<div class="w-56">
					<FormControl
						type="select"
						:model-value="colorScheme"
						:options="THEMES"
						@update:model-value="setColorScheme"
					/>
				</div>
			</SettingsRow>
		</div>
	</SettingsBody>
</template>

<script setup>
import { computed } from "vue"
import {
	FormControl,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
	call,
	createResource,
	toast,
	useColorScheme,
} from "frappe-ui"
import { session } from "@/data/session"
import { errorMessage } from "@/utils"

const THEMES = [
	{ label: "Light", value: "light" },
	{ label: "Dark", value: "dark" },
	{ label: "Automatic", value: "system" },
]

const { colorScheme, setColorScheme } = useColorScheme()

const user = createResource({
	url: "frappe.client.get_value",
	params: { doctype: "User", filters: { name: session.user }, fieldname: ["language", "time_zone"] },
	auto: true,
})

const languages = createResource({
	url: "frappe.client.get_list",
	params: { doctype: "Language", fields: ["name", "language_name"], filters: { enabled: 1 }, limit_page_length: 0, order_by: "language_name asc" },
	auto: true,
	transform: (rows) => rows.map((l) => ({ label: l.language_name, value: l.name })),
})

// Users without a language of their own see the site's.
const siteLanguage = createResource({
	url: "frappe.client.get_single_value",
	params: { doctype: "System Settings", field: "language" },
	auto: true,
})

const timeZones = createResource({ url: "frappe.core.doctype.user.user.get_timezones", auto: true })
const timeZoneOptions = computed(() => (timeZones.data?.timezones || []).map((tz) => ({ label: tz, value: tz })))

async function save(fieldname, value) {
	if (!value || value === user.data?.[fieldname]) return
	try {
		await call("frappe.client.set_value", { doctype: "User", name: session.user, fieldname: { [fieldname]: value } })
		user.data[fieldname] = value
		// A new language only takes effect once the page reloads.
		toast.success(fieldname === "language" ? "Language saved. Reload to apply it." : "Time zone saved")
	} catch (e) {
		toast.error(errorMessage(e))
	}
}
</script>
