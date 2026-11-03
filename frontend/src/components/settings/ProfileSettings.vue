<template>
	<SettingsHeader title="Profile" />
	<SettingsBody>
		<div v-if="user.data" class="flex flex-col gap-6 pt-6">
			<FileUploader
				file-types="image/png,image/jpeg,image/jpg"
				:private="false"
				@success="(file) => save({ user_image: file.file_url }, 'Profile picture updated')"
			>
				<template #default="{ openFileSelector, uploading }">
					<div class="flex items-center gap-4">
						<button
							type="button"
							class="flex rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
							aria-label="Change profile picture"
							:disabled="uploading"
							@click="openFileSelector"
						>
							<Avatar :image="user.data.user_image" :label="displayName" size="3xl" class="!h-16 !w-16" />
						</button>
						<div class="flex min-w-0 flex-col gap-1">
							<div class="truncate text-xl-semibold text-ink-gray-8">{{ displayName }}</div>
							<p class="truncate text-base text-ink-gray-6">
								{{ uploading ? "Uploading…" : user.data.email }}
							</p>
						</div>
					</div>
				</template>
			</FileUploader>

			<div class="grid gap-6 sm:grid-cols-2">
				<FormControl
					v-model="user.data.first_name"
					label="First name"
					variant="outline"
					autocomplete="given-name"
					@blur="saveName"
				/>
				<FormControl
					v-model="user.data.last_name"
					label="Last name"
					variant="outline"
					autocomplete="family-name"
					@blur="saveName"
				/>
			</div>

			<SettingsRow title="Password" description="Manage password and account access">
				<Button label="Update Password" @click="passwordDialog = true" />
			</SettingsRow>
		</div>
	</SettingsBody>

	<Dialog v-model:open="passwordDialog" title="Update password">
		<form class="flex flex-col gap-4" @submit.prevent="updatePassword">
			<FormControl
				v-model="password.current"
				type="password"
				label="Current password"
				autocomplete="current-password"
				variant="outline"
			/>
			<FormControl
				v-model="password.next"
				type="password"
				label="New password"
				autocomplete="new-password"
				variant="outline"
			/>
			<ErrorMessage :message="password.error" />
		</form>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button label="Cancel" @click="passwordDialog = false" />
				<Button label="Update" variant="solid" :loading="password.saving" @click="updatePassword" />
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue"
import {
	Avatar,
	Button,
	Dialog,
	ErrorMessage,
	FileUploader,
	FormControl,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
	call,
	createResource,
	toast,
} from "frappe-ui"
import { session } from "@/data/session"
import { errorMessage } from "@/utils"

const user = createResource({
	url: "frappe.client.get_value",
	params: {
		doctype: "User",
		filters: { name: session.user },
		fieldname: ["first_name", "last_name", "email", "user_image"],
	},
	auto: true,
	// A copy of what was loaded, to tell a real name change from a plain blur.
	onSuccess: (data) => (user.originalData = { ...data }),
})

const passwordDialog = ref(false)
const password = reactive({ current: "", next: "", error: "", saving: false })

const displayName = computed(() =>
	[user.data?.first_name, user.data?.last_name].filter(Boolean).join(" ") || session.user,
)

watch(passwordDialog, (open) => {
	if (open) Object.assign(password, { current: "", next: "", error: "" })
})

async function save(values, message) {
	try {
		await call("frappe.client.set_value", { doctype: "User", name: session.user, fieldname: values })
		// Keep the sidebar header and avatars in step with the profile.
		if ("user_image" in values) session.userImage = values.user_image
		session.fullName = displayName.value
		toast.success(message)
	} catch (e) {
		toast.error(errorMessage(e))
		user.reload()
	}
}

// Blur can fire more than once per field, and two saves of one User clash on the server,
// so only a real change that isn't already being saved goes out.
let savedName = null
let savingName = false

async function saveName() {
	const first = user.data.first_name?.trim() || ""
	const last = user.data.last_name?.trim() || ""
	if (!first) {
		toast.error("First name is required")
		return
	}
	savedName ??= `${user.originalData?.first_name || ""}|${user.originalData?.last_name || ""}`
	if (savingName || `${first}|${last}` === savedName) return
	savingName = true
	try {
		await save({ first_name: first, last_name: last }, "Name saved")
		savedName = `${first}|${last}`
	} finally {
		savingName = false
	}
}

async function updatePassword() {
	if (!password.current || !password.next) {
		password.error = "Enter your current and new password"
		return
	}
	password.saving = true
	password.error = ""
	try {
		await call("frappe.core.doctype.user.user.update_password", {
			old_password: password.current,
			new_password: password.next,
		})
		passwordDialog.value = false
		toast.success("Password updated")
	} catch (e) {
		password.error = errorMessage(e)
	} finally {
		password.saving = false
	}
}
</script>
