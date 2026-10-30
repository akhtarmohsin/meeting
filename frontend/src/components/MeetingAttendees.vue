<template>
	<div>
		<div class="mb-3 flex flex-wrap gap-2 text-sm">
			<Badge v-for="(count, rsvp) in summary" :key="rsvp" :theme="RSVP_THEME[rsvp]" :label="`${count} ${rsvp}`" />
		</div>
		<div class="divide-y rounded-lg border">
			<div v-for="a in doc.attendees" :key="a.name" class="flex items-center gap-3 px-4 py-2.5">
				<Avatar :label="a.full_name || a.email" size="md" />
				<div class="min-w-0 flex-1">
					<div class="flex items-center gap-2 truncate text-base text-ink-gray-9">
						{{ a.full_name || a.email }}
						<span v-if="a.user === doc.organizer" class="text-sm text-ink-gray-5">Organizer</span>
						<span v-else-if="a.optional" class="text-sm text-ink-gray-5">Optional</span>
					</div>
					<div class="truncate text-sm text-ink-gray-5">{{ a.email }}</div>
				</div>
				<Badge :label="a.rsvp" :theme="RSVP_THEME[a.rsvp]" />
				<label v-if="canEdit && doc.status !== 'Scheduled'" class="flex items-center gap-1.5 text-sm text-ink-gray-6">
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

const summary = computed(() => {
	const counts = {}
	for (const a of props.doc.attendees) counts[a.rsvp] = (counts[a.rsvp] || 0) + 1
	return counts
})

function toggleAttended(attendee, checked) {
	const attendees = props.doc.attendees.map((a) => (a.name === attendee.name ? { ...a, attended: checked ? 1 : 0 } : a))
	props.save({ attendees })
}
</script>
