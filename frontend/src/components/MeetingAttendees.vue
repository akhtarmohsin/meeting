<template>
	<div class="flex flex-col gap-2">
		<p class="text-sm text-ink-gray-6">{{ summaryText }}</p>
		<div class="flex flex-col divide-y divide-outline-gray-1">
			<div v-for="a in doc.attendees" :key="a.name" class="flex items-center gap-3 py-3">
				<Avatar :label="a.full_name || a.email" size="md" class="shrink-0" />
				<div class="min-w-0 flex-1">
					<div class="flex items-center gap-2 text-base font-medium text-ink-gray-9">
						<span class="truncate">{{ a.full_name || a.email }}</span>
						<span v-if="a.user === doc.organizer" class="shrink-0 text-sm font-normal text-ink-gray-6">Organizer</span>
						<span v-else-if="a.optional" class="shrink-0 text-sm font-normal text-ink-gray-6">Optional</span>
					</div>
					<div class="truncate text-sm text-ink-gray-6">{{ a.email }}</div>
				</div>
				<div class="flex w-20 shrink-0 justify-end">
					<Badge :label="a.rsvp" :theme="RSVP_THEME[a.rsvp]" />
				</div>
				<label
					v-if="showAttended"
					class="flex w-24 shrink-0 cursor-pointer items-center justify-end gap-1.5 text-sm text-ink-gray-7"
				>
					<input type="checkbox" :checked="a.attended" @change="toggleAttended(a, $event.target.checked)" />
					Attended
				</label>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { Avatar, Badge } from "frappe-ui"
import { RSVP_THEME } from "@/utils"

const props = defineProps({ doc: Object, canEdit: Boolean, save: Function })

const RSVP_ORDER = ["Accepted", "Tentative", "Declined", "Pending"]

const summaryText = computed(() => {
	const counts = {}
	for (const a of props.doc.attendees) counts[a.rsvp] = (counts[a.rsvp] || 0) + 1
	return RSVP_ORDER.filter((r) => counts[r])
		.map((r) => `${counts[r]} ${r.toLowerCase()}`)
		.join(" · ")
})

const showAttended = computed(() => props.canEdit && props.doc.status !== "Scheduled")

function toggleAttended(attendee, checked) {
	const attendees = props.doc.attendees.map((a) => (a.name === attendee.name ? { ...a, attended: checked ? 1 : 0 } : a))
	props.save({ attendees })
}
</script>
