<template>
	<header class="page-header">
		<h1 class="text-lg-semibold text-ink-gray-9">Home</h1>
		<Button variant="solid" :route="{ name: 'NewMeeting' }">
			<template #prefix><Icon name="lucide-plus" class="h-4 w-4" /></template>
			New meeting
		</Button>
	</header>
	<div class="page flex flex-col gap-10">
		<div class="flex flex-col gap-1">
			<h2 class="text-3xl-semibold leading-tight text-ink-gray-9">{{ greeting }}, {{ firstName }}</h2>
			<p class="text-base text-ink-gray-6">{{ formatDate(new Date(), "dddd, D MMMM YYYY") }}</p>
		</div>

		<div class="grid grid-cols-2 gap-y-5 sm:flex sm:divide-x sm:divide-outline-gray-2">
			<StatCard label="Meetings today" :value="data?.today.length" />
			<StatCard label="Awaiting your RSVP" :value="data?.pending_rsvp" />
			<StatCard label="Open action items" :value="data?.open_action_items" :to="{ name: 'ActionItems' }" />
			<StatCard
				label="Overdue"
				:value="data?.overdue_action_items"
				:danger="data?.overdue_action_items > 0"
				:to="{ name: 'ActionItems' }"
			/>
		</div>

		<section>
			<h3 class="pb-1 text-base-semibold text-ink-gray-9">Today</h3>
			<div v-if="dashboard.error" class="text-base text-ink-red-8">{{ errorMessage(dashboard.error) }}</div>
			<div v-else-if="dashboard.loading && !data" class="text-base text-ink-gray-5">Loading…</div>
			<EmptyState
				v-else-if="!data?.today.length"
				icon="lucide-sun"
				title="Nothing scheduled today"
				action="Schedule a meeting"
				:to="{ name: 'NewMeeting' }"
			/>
			<div v-else class="flex flex-col">
				<MeetingRow v-for="m in data.today" :key="m.name" :meeting="m" show-join />
			</div>
		</section>

		<section v-if="upcomingLater.length">
			<div class="flex items-center justify-between pb-1">
				<h3 class="text-base-semibold text-ink-gray-9">Coming up</h3>
				<Button variant="ghost" :route="{ name: 'Meetings' }">View all</Button>
			</div>
			<div v-for="group in groupByDay(upcomingLater)" :key="group.label" class="flex flex-col pt-3">
				<div class="text-sm-medium text-ink-gray-6">{{ group.label }}</div>
				<div class="flex flex-col">
					<MeetingRow v-for="m in group.meetings" :key="m.name" :meeting="m" />
				</div>
			</div>
		</section>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { Button, Icon, createResource } from "frappe-ui"
import dayjs from "dayjs"
import EmptyState from "@/components/EmptyState.vue"
import MeetingRow from "@/components/MeetingRow.vue"
import StatCard from "@/components/StatCard.vue"
import { session } from "@/data/session"
import { errorMessage, formatDate, groupByDay } from "@/utils"

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
