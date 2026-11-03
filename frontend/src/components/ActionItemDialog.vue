<template>
	<Dialog v-model:open="show" :title="item?.name ? 'Edit action item' : 'New action item'">
		<template #default>
			<div class="space-y-4">
				<FormControl v-model="form.title" label="Title" placeholder="Share the revised roadmap" />
				<div class="grid grid-cols-2 gap-4">
					<FormControl v-model="form.status" type="select" label="Status" :options="statuses" />
					<FormControl v-model="form.priority" type="select" label="Priority" :options="priorities" />
				</div>
				<div class="grid grid-cols-2 gap-4">
					<FormControl
						v-model="form.assigned_to"
						type="select"
						label="Assigned to"
						:options="assigneeOptions"
					/>
					<FormControl v-model="form.due_date" type="date" label="Due date" />
				</div>
				<FormControl v-model="form.description" type="textarea" label="Details" :rows="3" />
				<ErrorMessage :message="error" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-between">
				<Button v-if="item?.name" theme="red" variant="ghost" @click="remove">Delete</Button>
				<div class="ml-auto flex gap-2">
					<Button @click="show = false">Cancel</Button>
					<Button variant="solid" :loading="saving" @click="save">Save</Button>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue"
import { Button, Dialog, ErrorMessage, FormControl, call, createResource } from "frappe-ui"
import { session } from "@/data/session"
import { errorMessage } from "@/utils"

const show = defineModel({ type: Boolean })
const props = defineProps({
	item: Object,
	meeting: String,
	// Meeting attendees, offered first when assigning.
	people: { type: Array, default: () => [] },
})
const emit = defineEmits(["saved"])

const statuses = ["Open", "In Progress", "Done", "Cancelled"]
const priorities = ["Low", "Medium", "High"]

const form = reactive({})
const saving = ref(false)
const error = ref("")

const users = createResource({ url: "meeting.api.meetings.search_users", params: { txt: "" } })

const assigneeOptions = computed(() => {
	const people = props.people.length ? props.people : users.data || []
	const options = people
		.filter((p) => p.user || p.name)
		.map((p) => ({ label: p.full_name || p.email, value: p.user || p.name }))
	// The default assignee is you, who the user search leaves out when you're Administrator.
	if (!options.some((o) => o.value === session.user)) {
		options.unshift({ label: session.fullName || session.user, value: session.user })
	}
	return [{ label: "Unassigned", value: "" }, ...options]
})

watch(show, (open) => {
	if (!open) return
	if (!props.people.length) users.fetch()
	error.value = ""
	Object.assign(form, {
		title: "",
		status: "Open",
		priority: "Medium",
		assigned_to: session.user,
		due_date: "",
		description: "",
		meeting: props.meeting || null,
		...props.item,
	})
})

async function save() {
	saving.value = true
	error.value = ""
	try {
		await call("meeting.api.action_items.save_action_item", { data: { ...form }, name: props.item?.name })
		show.value = false
		emit("saved")
	} catch (e) {
		error.value = errorMessage(e)
	} finally {
		saving.value = false
	}
}

async function remove() {
	await call("meeting.api.action_items.delete_action_item", { name: props.item.name })
	show.value = false
	emit("saved")
}
</script>
