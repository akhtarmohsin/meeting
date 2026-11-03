<template>
	<SettingsHeader title="Users" description="People who can use Meeting">
		<template #actions>
			<Button icon-left="lucide-plus" label="Add user" @click="openAddDialog" />
		</template>
	</SettingsHeader>
	<SettingsBody>
		<div class="flex flex-col gap-3 pt-6">
			<div class="w-72">
				<TextInput v-model="search" placeholder="Search by name or email">
					<template #prefix><Icon name="lucide-search" class="size-4 text-ink-gray-4" /></template>
				</TextInput>
			</div>
			<p v-if="users.loading && !users.data" class="text-base text-ink-gray-6">Loading…</p>
			<p v-else-if="!filtered.length" class="py-6 text-center text-base text-ink-gray-6">
				{{ search ? "No one matches your search" : "No users yet" }}
			</p>
			<div v-else class="flex flex-col divide-y divide-outline-gray-1">
				<div v-for="user in filtered" :key="user.name" class="flex items-center gap-3 py-2.5">
					<Avatar size="lg" :image="user.user_image" :label="user.full_name || user.email" class="shrink-0" />
					<div class="min-w-0 flex-1">
						<div class="truncate text-base text-ink-gray-8">{{ user.full_name || user.email }}</div>
						<div class="truncate text-sm text-ink-gray-6">{{ user.email }}</div>
					</div>
					<Badge v-if="!user.enabled" label="Disabled" theme="gray" variant="outline" />
					<Badge v-if="user.role === 'Meeting Manager'" label="Manager" theme="blue" variant="outline" />
				</div>
			</div>
		</div>
	</SettingsBody>

	<Dialog v-model:open="addDialog" title="Add user">
		<form class="flex flex-col gap-4" @submit.prevent="addUser">
			<div class="grid grid-cols-2 gap-4">
				<FormControl v-model="form.first_name" label="First name" variant="outline" />
				<FormControl v-model="form.last_name" label="Last name" variant="outline" />
			</div>
			<FormControl v-model="form.email" type="email" label="Email" placeholder="name@company.com" variant="outline" />
			<FormControl v-model="form.role" type="select" label="Role" :options="roleOptions" />
			<Checkbox v-model="form.send_welcome_email" label="Send a welcome email to set their password" />
			<ErrorMessage :message="form.error" />
		</form>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button label="Cancel" @click="addDialog = false" />
				<Button label="Add user" variant="solid" :loading="form.saving" @click="addUser" />
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, reactive, ref } from "vue"
import {
	Avatar,
	Badge,
	Button,
	Checkbox,
	Dialog,
	ErrorMessage,
	FormControl,
	Icon,
	SettingsBody,
	SettingsHeader,
	TextInput,
	call,
	createResource,
	toast,
} from "frappe-ui"
import { session } from "@/data/session"
import { errorMessage } from "@/utils"

const users = createResource({ url: "meeting.api.users.get_users", auto: true })
const search = ref("")
const addDialog = ref(false)
const form = reactive({})

// The server only lets System Managers hand out the manager role; offer it to them alone.
const roleOptions = computed(() => [
	{ label: "Meeting User", value: "Meeting User" },
	...(session.isSystemManager ? [{ label: "Meeting Manager", value: "Meeting Manager" }] : []),
])

const filtered = computed(() => {
	const query = search.value.trim().toLowerCase()
	return (users.data || []).filter(
		(u) => !query || `${u.full_name} ${u.email}`.toLowerCase().includes(query),
	)
})

function openAddDialog() {
	Object.assign(form, {
		first_name: "",
		last_name: "",
		email: search.value.includes("@") ? search.value.trim() : "",
		role: "Meeting User",
		send_welcome_email: true,
		error: "",
		saving: false,
	})
	addDialog.value = true
}

async function addUser() {
	form.error = ""
	form.saving = true
	try {
		const { created } = await call("meeting.api.users.create_user", {
			email: form.email,
			first_name: form.first_name,
			last_name: form.last_name,
			role: form.role,
			send_welcome_email: form.send_welcome_email,
		})
		addDialog.value = false
		toast.success(created ? `${form.email} added` : `${form.email} already had an account; added to Meeting`)
		users.reload()
	} catch (e) {
		form.error = errorMessage(e)
	} finally {
		form.saving = false
	}
}
</script>
