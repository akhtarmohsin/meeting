<template>
	<header class="page-header">
		<h1 class="text-lg font-semibold text-ink-gray-9">Meetings</h1>
		<Button variant="solid" :route="{ name: 'NewMeeting' }">
			<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
			New
		</Button>
	</header>
	<div class="page">
		<div class="mb-5 flex flex-wrap items-center gap-3">
			<TabButtons v-model="view" :buttons="views" />
			<TextInput v-model="search" placeholder="Search meetings" class="w-full sm:ml-auto sm:w-64">
				<template #prefix><FeatherIcon name="search" class="h-4 w-4" /></template>
			</TextInput>
		</div>

		<div v-if="meetings.error" class="text-base text-ink-red-4">{{ errorMessage(meetings.error) }}</div>
		<div v-else-if="meetings.loading && !meetings.data" class="text-base text-ink-gray-5">Loading…</div>
		<EmptyState
			v-else-if="!meetings.data?.length"
			icon="calendar"
			:title="search ? 'No meetings match your search' : `No ${view} meetings`"
			action="Schedule a meeting"
			:to="{ name: 'NewMeeting' }"
		/>
		<div v-for="group in groups" v-else :key="group.label" class="mb-6">
			<div class="mb-2 text-sm font-medium text-ink-gray-5">{{ group.label }}</div>
			<div class="space-y-2">
				<MeetingRow
					v-for="m in group.meetings"
					:key="m.name"
					:meeting="m"
					:show-join="view === 'upcoming'"
				/>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Button, FeatherIcon, TabButtons, TextInput, createResource, debounce } from "frappe-ui"
import EmptyState from "@/components/EmptyState.vue"
import MeetingRow from "@/components/MeetingRow.vue"
import { errorMessage, groupByDay } from "@/utils"

const views = [
	{ label: "Upcoming", value: "upcoming" },
	{ label: "Past", value: "past" },
	{ label: "All", value: "all" },
]
const view = ref("upcoming")
const search = ref("")

const meetings = createResource({
	url: "meeting.api.meetings.get_meetings",
	makeParams: () => ({ view: view.value, search: search.value || null }),
	auto: true,
})

watch(view, () => meetings.reload())
watch(search, debounce(() => meetings.reload(), 300))

const groups = computed(() => groupByDay(meetings.data || []))
</script>
