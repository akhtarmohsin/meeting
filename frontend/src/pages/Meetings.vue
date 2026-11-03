<template>
	<header class="page-header">
		<h1 class="text-lg-semibold text-ink-gray-9">Meetings</h1>
		<Button variant="solid" :route="{ name: 'NewMeeting' }">
			<template #prefix><Icon name="lucide-plus" class="h-4 w-4" /></template>
			New
		</Button>
	</header>
	<div class="page flex flex-col gap-6">
		<div class="flex flex-wrap items-center gap-3">
			<TabButtons v-model="view" :options="views" />
			<TextInput
				v-model="search"
				placeholder="Search meetings"
				class="w-full sm:ml-auto sm:w-64"
			>
				<template #prefix><Icon name="lucide-search" class="h-4 w-4" /></template>
			</TextInput>
		</div>

		<div v-if="meetings.error" class="text-base text-ink-red-8">
			{{ errorMessage(meetings.error) }}
		</div>
		<div v-else-if="meetings.loading && !meetings.data" class="text-base text-ink-gray-5">
			Loading…
		</div>
		<EmptyState
			v-else-if="!meetings.data?.length"
			icon="lucide-calendar"
			:title="search ? 'No meetings match your search' : EMPTY[view]"
			action="Schedule a meeting"
			:to="{ name: 'NewMeeting' }"
		/>
		<div v-for="group in groups" v-else :key="group.label" class="flex flex-col">
			<div class="text-sm-medium text-ink-gray-6">{{ group.label }}</div>
			<div class="flex flex-col">
				<MeetingRow
					v-for="m in group.meetings"
					:key="m.name"
					:meeting="m"
					:show-join="['upcoming', 'awaiting_reply'].includes(view)"
				/>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { Button, Icon, TabButtons, TextInput, createResource, debounce } from "frappe-ui";
import EmptyState from "@/components/EmptyState.vue";
import MeetingRow from "@/components/MeetingRow.vue";
import { errorMessage, groupByDay } from "@/utils";

const views = [
	{ label: "Upcoming", value: "upcoming" },
	{ label: "Past", value: "past" },
	{ label: "Awaiting reply", value: "awaiting_reply" },
	{ label: "Minutes pending", value: "minutes_pending" },
	{ label: "All", value: "all" },
];
const EMPTY = {
	upcoming: "No upcoming meetings",
	past: "No past meetings",
	awaiting_reply: "You've replied to every invitation",
	minutes_pending: "Every meeting you ran has its minutes",
	all: "No meetings yet",
};
// Home's stat cards link here with ?view=awaiting_reply or ?view=minutes_pending.
const route = useRoute();
const view = ref(views.some((v) => v.value === route.query.view) ? route.query.view : "upcoming");
const search = ref("");

const meetings = createResource({
	url: "meeting.api.meetings.get_meetings",
	makeParams: () => ({ view: view.value, search: search.value || null }),
	auto: true,
});

watch(view, () => meetings.reload());
watch(
	search,
	debounce(() => meetings.reload(), 300)
);

const groups = computed(() => groupByDay(meetings.data || []));
</script>
