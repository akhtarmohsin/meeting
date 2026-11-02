<template>
	<header class="page-header">
		<h1 class="text-lg font-semibold text-ink-gray-9">{{ name ? "Edit meeting" : "New meeting" }}</h1>
		<div class="flex gap-2">
			<Button @click="router.back()">Cancel</Button>
			<Button variant="solid" :loading="saving" @click="save">Save</Button>
		</div>
	</header>
	<div v-if="loaded" class="page max-w-3xl space-y-6">
		<FormControl v-model="form.title" label="Title" placeholder="Weekly product sync" autofocus />

		<div class="grid gap-4 sm:grid-cols-2 md:gap-x-8">
			<FormControl v-model="start" type="datetime-local" label="Starts" />
			<FormControl v-model="end" type="datetime-local" label="Ends" />
		</div>

		<!-- Where the meeting happens on the left, the description beside it. -->
		<div class="grid gap-8 md:grid-cols-2">
			<div class="flex min-w-0 flex-col gap-4">
				<FormControl v-model="form.meeting_type" type="select" label="Type" :options="meetingTypes" />
				<FormControl
					v-if="form.meeting_type !== 'Online'"
					v-model="form.location"
					label="Location"
					placeholder="Conference room A"
				/>
				<template v-if="form.meeting_type !== 'In Person'">
					<FormControl v-model="form.video_provider" type="select" label="Video" :options="providers" />
					<FormControl v-model="form.video_link" label="Meeting link" placeholder="https://meet.google.com/..." />
				</template>
				<div v-if="showMeetButton" class="flex items-center gap-3">
					<Button :loading="generatingLink" @click="generateMeetLink">
						<template #prefix><FeatherIcon name="video" class="h-4 w-4" /></template>
						{{ form.meet_room ? "Generate new Frappe Meet link" : "Generate Frappe Meet link" }}
					</Button>
					<span v-if="form.meet_room" class="truncate text-sm text-ink-gray-6">Room {{ form.meet_room }}</span>
				</div>
			</div>
			<div class="flex min-w-0 flex-col gap-4">
				<div
					v-if="session.frappeCalendarAvailable"
					class="flex items-center gap-3 rounded-lg border border-outline-gray-2 px-3 py-2.5"
				>
					<FeatherIcon name="calendar" class="h-4 w-4 shrink-0 text-ink-gray-6" />
					<span class="flex-1 text-base text-ink-gray-8">Add to Frappe Calendar</span>
					<Switch
						:model-value="Boolean(form.add_to_calendar)"
						@update:model-value="(on) => (form.add_to_calendar = on ? 1 : 0)"
					/>
				</div>
				<FormControl
					v-model="form.description"
					type="textarea"
					label="Description"
					placeholder="What should people know before the meeting?"
					:rows="session.frappeCalendarAvailable ? 7 : 9"
				/>
			</div>
		</div>

		<!-- Attendees and agenda side by side on wide screens, stacked on small ones. -->
		<div class="grid gap-8 md:grid-cols-2">
			<section class="min-w-0">
				<div class="mb-2 flex h-7 items-center text-sm text-ink-gray-6">Attendees</div>
				<UserPicker @select="addAttendee" />
				<div v-if="form.attendees.length" class="mt-1 flex flex-col divide-y divide-outline-gray-1">
					<div v-for="(a, i) in form.attendees" :key="a.email" class="flex items-center gap-3 py-2.5">
						<Avatar :label="a.full_name || a.email" size="sm" class="shrink-0" />
						<div class="min-w-0 flex-1">
							<div class="truncate text-base text-ink-gray-9">{{ a.full_name || a.email }}</div>
							<div v-if="a.full_name" class="truncate text-sm text-ink-gray-6">{{ a.email }}</div>
						</div>
						<!-- Fixed lanes: role/optional, then remove; the organizer row leaves remove empty. -->
						<div class="flex w-24 shrink-0 justify-end">
							<span v-if="a.user === form.organizer" class="text-sm text-ink-gray-6">Organizer</span>
							<Checkbox
								v-else
								label="Optional"
								:model-value="Boolean(a.optional)"
								@update:model-value="(checked) => (a.optional = checked ? 1 : 0)"
							/>
						</div>
						<div class="flex w-7 shrink-0 justify-end">
							<Button
								v-if="a.user !== form.organizer"
								variant="ghost"
								size="sm"
								:aria-label="`Remove ${a.full_name || a.email}`"
								@click="form.attendees.splice(i, 1)"
							>
								<template #icon><FeatherIcon name="x" class="h-4 w-4" /></template>
							</Button>
						</div>
					</div>
				</div>
			</section>

			<AgendaEditor v-model="form.agenda" class="min-w-0" />
		</div>

		<Checkbox v-if="!name" v-model="sendInvites" label="Email invites to attendees after saving" />
		<ErrorMessage :message="error" />
	</div>
</template>

<script setup>
import { computed, reactive, ref } from "vue"
import { useRouter } from "vue-router"
import dayjs from "dayjs"
import { Avatar, Button, Checkbox, ErrorMessage, FeatherIcon, FormControl, Switch, call, toast } from "frappe-ui"
import AgendaEditor from "@/components/AgendaEditor.vue"
import UserPicker from "@/components/UserPicker.vue"
import { session } from "@/data/session"
import { errorMessage, fromInputDatetime, toInputDatetime } from "@/utils"

const props = defineProps({ name: String })
const router = useRouter()

const meetingTypes = ["Online", "In Person", "Hybrid"]
const providers = [
	"",
	...(session.frappeMeetAvailable ? ["Frappe Meet"] : []),
	"Google Meet",
	"Zoom",
	"Microsoft Teams",
	"Jitsi",
	"Other",
]

const form = reactive(blankMeeting())
const loaded = ref(!props.name)
const saving = ref(false)
const generatingLink = ref(false)
const sendInvites = ref(true)
const error = ref("")

if (props.name) loadMeeting()

const start = computed({
	get: () => toInputDatetime(form.start),
	set: (v) => {
		// Keep the meeting length when the start moves.
		const length = dayjs(form.end).diff(dayjs(form.start), "minute") || 30
		form.start = fromInputDatetime(v)
		form.end = fromInputDatetime(dayjs(v).add(length, "minute"))
	},
})
const end = computed({
	get: () => toInputDatetime(form.end),
	set: (v) => (form.end = fromInputDatetime(v)),
})

const showMeetButton = computed(
	() => session.frappeMeetAvailable && form.meeting_type !== "In Person" && form.video_provider === "Frappe Meet",
)

async function generateMeetLink() {
	if (form.video_link && !window.confirm("Replace the current link with a new Frappe Meet link?")) return
	error.value = ""
	generatingLink.value = true
	try {
		const room = await call("meeting.api.meetings.create_frappe_meet_link", { title: form.title || null })
		Object.assign(form, room)
	} catch (e) {
		error.value = errorMessage(e)
	} finally {
		generatingLink.value = false
	}
}

function addAttendee(person) {
	if (form.attendees.some((a) => a.email === person.email)) return
	form.attendees.push({ ...person, rsvp: "Pending", optional: 0 })
}

async function loadMeeting() {
	const { doc } = await call("meeting.api.meetings.get_meeting", { name: props.name })
	Object.assign(form, doc)
	loaded.value = true
}

async function save() {
	error.value = ""
	saving.value = true
	try {
		const data = { ...form, agenda: form.agenda.filter((a) => a.topic?.trim()) }
		const name = await call("meeting.api.meetings.save_meeting", { data, name: props.name })
		if (!props.name && sendInvites.value) {
			const sent = await call("meeting.api.meetings.send_invites", { name })
			if (sent) toast({ title: `Invites sent to ${sent} attendee${sent > 1 ? "s" : ""}`, icon: "mail" })
		}
		router.replace({ name: "Meeting", params: { name } })
	} catch (e) {
		error.value = errorMessage(e)
	} finally {
		saving.value = false
	}
}

function blankMeeting() {
	const start = dayjs().add(30 - (dayjs().minute() % 30), "minute").second(0)
	return {
		title: "",
		organizer: session.user,
		status: "Scheduled",
		meeting_type: "Online",
		start: fromInputDatetime(start),
		end: fromInputDatetime(start.add(30, "minute")),
		location: "",
		video_provider: session.frappeMeetAvailable ? "Frappe Meet" : "",
		video_link: "",
		meet_room: "",
		add_to_calendar: 0,
		description: "",
		attendees: [
			{ user: session.user, email: session.user, full_name: session.fullName, rsvp: "Accepted", optional: 0 },
		],
		agenda: [],
	}
}
</script>
