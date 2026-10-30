<template>
	<router-link
		:to="{ name: 'Meeting', params: { name: meeting.name } }"
		class="flex items-center gap-4 rounded-lg border px-4 py-3 hover:bg-surface-gray-1"
	>
		<div class="w-24 shrink-0 text-sm">
			<div class="font-medium text-ink-gray-9">{{ formatTime(meeting.start) }}</div>
			<div class="text-ink-gray-5">{{ formatTime(meeting.end) }}</div>
		</div>
		<div class="min-w-0 flex-1">
			<div class="flex items-center gap-2">
				<span class="truncate text-base font-medium text-ink-gray-9">{{ meeting.title }}</span>
				<Badge
					v-if="meeting.status !== 'Scheduled'"
					:label="meeting.status"
					:theme="MEETING_STATUS_THEME[meeting.status]"
				/>
			</div>
			<div class="mt-1 flex items-center gap-1.5 text-sm text-ink-gray-5">
				<FeatherIcon :name="meeting.video_link ? 'video' : 'map-pin'" class="h-3.5 w-3.5" />
				<span class="truncate">{{ where }}</span>
			</div>
		</div>
		<div class="hidden items-center -space-x-1.5 sm:flex">
			<Avatar
				v-for="a in meeting.attendees.slice(0, 4)"
				:key="a.email"
				:label="a.full_name || a.email"
				size="sm"
				class="ring-2 ring-surface-white"
			/>
			<span v-if="meeting.attendees.length > 4" class="pl-3 text-sm text-ink-gray-5">
				+{{ meeting.attendees.length - 4 }}
			</span>
		</div>
		<Button
			v-if="showJoin && meeting.video_link"
			size="sm"
			variant="subtle"
			@click.prevent="openLink(meeting.video_link)"
		>
			Join
		</Button>
	</router-link>
</template>

<script setup>
import { computed } from "vue"
import { Avatar, Badge, Button, FeatherIcon } from "frappe-ui"
import { MEETING_STATUS_THEME, formatTime } from "@/utils"

const props = defineProps({
	meeting: { type: Object, required: true },
	showJoin: { type: Boolean, default: false },
})

const where = computed(() => {
	const m = props.meeting
	if (m.video_link) return m.video_provider || "Online"
	return m.location || m.meeting_type
})

function openLink(url) {
	window.open(url, "_blank", "noopener")
}
</script>
