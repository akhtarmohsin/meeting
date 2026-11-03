<template>
	<header class="page-header">
		<div class="flex min-w-0 items-center gap-2 text-lg">
			<router-link :to="{ name: 'Meetings' }" class="text-ink-gray-5 hover:text-ink-gray-7">Meetings</router-link>
			<Icon name="lucide-chevron-right" class="h-4 w-4 text-ink-gray-4" />
			<span class="truncate font-semibold text-ink-gray-9">{{ doc?.title || name }}</span>
		</div>
		<div v-if="meeting.data" class="flex gap-2">
			<Button v-if="doc.video_link" variant="solid" @click="openLink(doc.video_link)">
				<template #prefix><Icon name="lucide-video" class="h-4 w-4" /></template>
				Join
			</Button>
			<Dropdown v-if="canEdit" :options="actions">
				<Button><template #icon><Icon name="lucide-ellipsis" class="h-4 w-4" /></template></Button>
			</Dropdown>
		</div>
	</header>

	<div v-if="meeting.error" class="page text-base text-ink-red-8">{{ errorMessage(meeting.error) }}</div>
	<div v-else-if="!doc" class="page text-base text-ink-gray-5">Loading…</div>
	<div v-else class="page space-y-6">
		<div>
			<div class="flex flex-wrap items-center gap-2">
				<h2 class="text-3xl-semibold text-ink-gray-9">{{ doc.title }}</h2>
				<Badge :label="doc.status" :theme="MEETING_STATUS_THEME[doc.status]" size="lg" />
			</div>
			<div class="mt-3 grid gap-2 text-base text-ink-gray-7 sm:grid-cols-2">
				<InfoLine icon="lucide-calendar">{{ formatDate(doc.start) }}</InfoLine>
				<InfoLine icon="lucide-clock">{{ formatRange(doc.start, doc.end) }}</InfoLine>
				<InfoLine v-if="doc.location" icon="lucide-map-pin">{{ doc.location }}</InfoLine>
				<InfoLine v-if="doc.video_link" icon="lucide-video">
					<a :href="doc.video_link" target="_blank" class="underline">{{ doc.video_provider || doc.video_link }}</a>
				</InfoLine>
				<InfoLine icon="lucide-user">Organized by {{ organizerName }}</InfoLine>
				<InfoLine v-if="meeting.data.series" icon="lucide-repeat">
					{{ meeting.data.series.message }} · meeting {{ meeting.data.series.index }} of {{ meeting.data.series.total }}
				</InfoLine>
				<InfoLine v-if="doc.invites_sent_on" icon="lucide-mail">Invites sent {{ formatDate(doc.invites_sent_on, "D MMM, h:mm A") }}</InfoLine>
			</div>
			<p v-if="doc.description" class="mt-4 whitespace-pre-line text-base text-ink-gray-7">{{ doc.description }}</p>
		</div>

		<RsvpBar v-if="showRsvp" :value="meeting.data.my_rsvp" :meeting="name" @change="meeting.reload()" />

		<TabButtons v-model="tab" :options="tabs" />

		<MeetingAttendees v-if="tab === 'attendees'" :doc="doc" :can-edit="canEdit" :save="save" />
		<MeetingAgenda v-else-if="tab === 'agenda'" :doc="doc" :can-edit="canEdit" :save="save" />
		<MeetingMinutes v-else-if="tab === 'minutes'" :doc="doc" :can-edit="canEdit" :save="save" />
		<ActionItemList
			v-else
			:items="meeting.data.action_items"
			:meeting="name"
			:people="doc.attendees"
			@changed="meeting.reload()"
		/>
	</div>
</template>

<script setup>
import { computed, ref } from "vue"
import { useRouter } from "vue-router"
import { Badge, Button, Dropdown, Icon, TabButtons, call, createResource, toast } from "frappe-ui"
import ActionItemList from "@/components/ActionItemList.vue"
import InfoLine from "@/components/InfoLine.vue"
import MeetingAgenda from "@/components/MeetingAgenda.vue"
import MeetingAttendees from "@/components/MeetingAttendees.vue"
import MeetingMinutes from "@/components/MeetingMinutes.vue"
import RsvpBar from "@/components/RsvpBar.vue"
import { session } from "@/data/session"
import { MEETING_STATUS_THEME, errorMessage, formatDate, formatRange } from "@/utils"

const props = defineProps({ name: String })
const router = useRouter()
const tab = ref("attendees")

const meeting = createResource({
	url: "meeting.api.meetings.get_meeting",
	params: { name: props.name },
	auto: true,
})

const doc = computed(() => meeting.data?.doc)
const canEdit = computed(() => meeting.data?.can_edit)
const showRsvp = computed(() => meeting.data?.my_rsvp && doc.value.organizer !== session.user && doc.value.status === "Scheduled")
const organizerName = computed(() => {
	const row = doc.value.attendees.find((a) => a.user === doc.value.organizer)
	return row?.full_name || doc.value.organizer
})

const tabs = computed(() => [
	{ label: `Attendees (${doc.value?.attendees.length || 0})`, value: "attendees" },
	{ label: `Agenda (${doc.value?.agenda.length || 0})`, value: "agenda" },
	{ label: "Minutes", value: "minutes" },
	{ label: `Action items (${meeting.data?.action_items.length || 0})`, value: "actions" },
])

const actions = computed(() => [
	{ label: "Edit", icon: "lucide-pencil", onClick: () => router.push({ name: "EditMeeting", params: { name: props.name } }) },
	{ label: doc.value?.invites_sent_on ? "Resend invites" : "Send invites", icon: "lucide-send", onClick: sendInvites },
	...statusActions.value,
	{ label: "Open in Desk", icon: "lucide-external-link", onClick: () => window.open(`/app/meeting/${props.name}`) },
	{ label: "Delete", icon: "lucide-trash-2", onClick: remove },
])

const statusActions = computed(() =>
	[
		["In Progress", "lucide-play"],
		["Completed", "lucide-circle-check"],
		["Cancelled", "lucide-circle-x"],
		["Scheduled", "lucide-rotate-ccw"],
	]
		.filter(([status]) => status !== doc.value?.status)
		.map(([status, icon]) => ({ label: `Mark ${status}`, icon, onClick: () => save({ status }) })),
)

async function save(values) {
	await call("meeting.api.meetings.save_meeting", { data: values, name: props.name })
	await meeting.reload()
	toast.success("Saved")
}

async function sendInvites() {
	const sent = await call("meeting.api.meetings.send_invites", { name: props.name })
	toast.success(sent ? `Invites sent to ${sent} attendee${sent > 1 ? "s" : ""}` : "No one to invite")
	meeting.reload()
}

async function remove() {
	if (!window.confirm("Delete this meeting?")) return
	await call("meeting.api.meetings.delete_meeting", { name: props.name })
	router.replace({ name: "Meetings" })
}

function openLink(url) {
	window.open(url, "_blank", "noopener")
}
</script>
