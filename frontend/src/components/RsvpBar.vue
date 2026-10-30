<template>
	<div class="flex flex-wrap items-center gap-3 rounded-lg bg-surface-gray-2 px-4 py-3">
		<span class="text-base text-ink-gray-7">
			{{ value === "Pending" ? "Will you attend?" : `You responded: ${value}` }}
		</span>
		<div class="ml-auto flex gap-2">
			<Button
				v-for="option in options"
				:key="option.value"
				:variant="value === option.value ? 'solid' : 'subtle'"
				:theme="value === option.value ? RSVP_THEME[option.value] : 'gray'"
				:loading="saving === option.value"
				@click="respond(option.value)"
			>
				{{ option.label }}
			</Button>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue"
import { Button, call } from "frappe-ui"
import { RSVP_THEME } from "@/utils"

const props = defineProps({ value: String, meeting: String })
const emit = defineEmits(["change"])

const options = [
	{ label: "Yes", value: "Accepted" },
	{ label: "Maybe", value: "Tentative" },
	{ label: "No", value: "Declined" },
]
const saving = ref(null)

async function respond(response) {
	saving.value = response
	try {
		await call("meeting.api.meetings.rsvp", { name: props.meeting, response })
		emit("change")
	} finally {
		saving.value = null
	}
}
</script>
