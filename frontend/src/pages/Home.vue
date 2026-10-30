<template>
	<header class="page-header">
		<h1 class="text-lg font-semibold text-ink-gray-9">Home</h1>
	</header>
	<div class="page space-y-8">
		<div>
			<h2 class="text-2xl font-semibold text-ink-gray-9">{{ greeting }}, {{ firstName }}</h2>
			<p class="mt-1 text-base text-ink-gray-5">{{ formatDate(new Date(), "dddd, D MMMM YYYY") }}</p>
		</div>

		<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
			<StatCard label="Meetings today" :value="data?.today.length" icon="calendar" />
			<StatCard label="Awaiting your RSVP" :value="data?.pending_rsvp" icon="mail" />
			<StatCard
				label="Open action items"
				:value="data?.open_action_items"
				icon="check-square"
				:to="{ name: 'ActionItems' }"
			/>
			<StatCard
				label="Overdue"
				:value="data?.overdue_action_items"
				icon="alert-circle"
				:danger="data?.overdue_action_items > 0"
				:to="{ name: 'ActionItems' }"
			/>
		</div>

		<section>
			<h3 class="mb-3 text-base font-semibold text-ink-gray-9">Today</h3>
			<div v-if="dashboard.loading && !data" class="text-base text-ink-gray-5">Loading…</div>
			<EmptyState
				v-else-if="!data?.today.length"
				icon="sun"
				title="Nothing scheduled today"
				action="Schedule a meeting"
				:to="{ name: 'NewMeeting' }"
			/>
			<div v-else class="space-y-2">
				<MeetingRow v-for="m in data.today" :key="m.name" :meeting="m" show-join />
			</div>
		</section>

		<section v-if="upcomingLater.length">
			<div class="mb-3 flex items-center justify-between">
				<h3 class="text-base font-semibold text-ink-gray-9">Coming up</h3>
				<Button variant="ghost" :route="{ name: 'Meetings' }">View all</Button>
			</div>
			<div v-for="group in groupByDay(upcomingLater)" :key="group.label" class="mb-4">
				<div class="mb-2 text-sm font-medium text-ink-gray-5">{{ group.label }}</div>
				<div class="space-y-2">
					<MeetingRow v-for="m in group.meetings" :key="m.name" :meeting="m" />
				</div>
			</div>
		</section>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { Button, createResource } from "frappe-ui"
import dayjs from "dayjs"
import EmptyState from "@/components/EmptyState.vue"
import MeetingRow from "@/components/MeetingRow.vue"
import StatCard from "@/components/StatCard.vue"
import { session } from "@/data/session"
import { formatDate, groupByDay } from "@/utils"

const dashboard = createResource({ url: "meeting.api.meetings.get_dashboard", auto: true })
const data = computed(() => dashboard.data)

const upcomingLater = computed(() => {
	const tomorrow = dayjs().add(1, "day").startOf("day")
	return (data.value?.upcoming || []).filter((m) => !dayjs(m.start).isBefore(tomorrow))
})

const firstName = computed(() => (session.fullName || "").split(" ")[0])
const greeting = computed(() => {
	const hour = new Date().getHours()
	if (hour < 12) return "Good morning"
	if (hour < 17) return "Good afternoon"
	return "Good evening"
})
</script>
