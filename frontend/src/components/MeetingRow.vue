<template>
	<router-link
		:to="{ name: 'Meeting', params: { name: meeting.name } }"
		class="-mx-3 flex items-center gap-4 rounded-5 px-3 py-3 hover:bg-surface-gray-1"
	>
		<div class="w-20 shrink-0 text-base tabular-nums">
			<div class="font-medium text-ink-gray-9">{{ formatTime(meeting.start) }}</div>
			<div class="text-ink-gray-5">{{ formatTime(meeting.end) }}</div>
		</div>
		<div class="min-w-0 flex-1">
			<div class="flex items-center gap-2">
				<span
					class="truncate text-base-medium"
					:class="
						meeting.status === 'Cancelled'
							? 'text-ink-gray-5 line-through'
							: 'text-ink-gray-9'
					"
				>
					{{ meeting.title }}
				</span>
				<Badge
					v-if="meeting.status !== 'Scheduled'"
					:label="meeting.status"
					:theme="MEETING_STATUS_THEME[meeting.status]"
				/>
			</div>
			<div class="mt-1 flex items-center gap-1.5 text-sm text-ink-gray-6">
				<Icon
					:name="isOnline ? 'lucide-video' : 'lucide-map-pin'"
					class="h-3.5 w-3.5 shrink-0"
				/>
				<span class="truncate">{{ where }}</span>
			</div>
		</div>
		<div class="hidden w-24 shrink-0 items-center justify-end gap-1 sm:flex">
			<Avatar
				v-for="a in meeting.attendees.slice(0, 3)"
				:key="a.email"
				:label="a.full_name || a.email"
				size="sm"
			/>
			<span v-if="meeting.attendees.length > 3" class="pl-0.5 text-sm text-ink-gray-6">
				+{{ meeting.attendees.length - 3 }}
			</span>
		</div>
		<!-- Fixed slot so rows with and without a link keep their columns aligned. -->
		<div v-if="showJoin" class="flex w-14 shrink-0 justify-end">
			<Button
				v-if="meeting.video_link"
				size="sm"
				@click.prevent="openLink(meeting.video_link)"
				>Join</Button
			>
		</div>
	</router-link>
</template>

<script setup>
import { computed } from "vue";
import { Avatar, Badge, Button, Icon } from "frappe-ui";
import { MEETING_STATUS_THEME, formatTime } from "@/utils";

const props = defineProps({
	meeting: { type: Object, required: true },
	showJoin: { type: Boolean, default: false },
});

const isOnline = computed(() => props.meeting.meeting_type !== "In Person");

const where = computed(() => {
	const m = props.meeting;
	if (m.video_link) return m.video_provider || "Online";
	return m.location || m.meeting_type;
});

function openLink(url) {
	window.open(url, "_blank", "noopener");
}
</script>
