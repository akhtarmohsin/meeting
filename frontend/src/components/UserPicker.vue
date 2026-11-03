<template>
	<div class="relative">
		<TextInput
			v-model="query"
			:placeholder="placeholder"
			@focus="open = true"
			@blur="closeSoon"
			@keydown.enter.prevent="pickTyped"
		>
			<template #prefix><Icon name="lucide-search" class="h-4 w-4" /></template>
		</TextInput>
		<div
			v-if="open && (results.data?.length || isEmail)"
			class="absolute z-20 mt-1 max-h-60 w-full overflow-y-auto rounded-6 border bg-surface-base p-1 shadow-lg"
		>
			<button
				v-for="u in results.data"
				:key="u.name"
				class="flex w-full items-center gap-2 rounded-4 px-2 py-1.5 text-left hover:bg-surface-gray-2"
				@mousedown.prevent="pick(u)"
			>
				<Avatar :label="u.full_name" :image="u.user_image" size="sm" />
				<div class="min-w-0">
					<div class="truncate text-base text-ink-gray-9">{{ u.full_name }}</div>
					<div class="truncate text-sm text-ink-gray-6">{{ u.email }}</div>
				</div>
			</button>
			<button
				v-if="isEmail"
				class="flex w-full items-center gap-2 rounded-4 px-2 py-1.5 text-left text-base hover:bg-surface-gray-2"
				@mousedown.prevent="pickTyped"
			>
				<Icon name="lucide-mail" class="h-4 w-4" />
				Invite {{ query }}
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Avatar, Icon, TextInput, createResource, debounce } from "frappe-ui"

defineProps({ placeholder: { type: String, default: "Add people by name or email" } })
const emit = defineEmits(["select"])

const query = ref("")
const open = ref(false)

const results = createResource({
	url: "meeting.api.meetings.search_users",
	makeParams: () => ({ txt: query.value }),
	auto: true,
})

watch(query, debounce(() => results.reload(), 250))

const isEmail = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(query.value.trim()))

function pick(user) {
	emit("select", { user: user.name, email: user.email, full_name: user.full_name })
	query.value = ""
}

function pickTyped() {
	const match = results.data?.[0]
	if (match && !isEmail.value) return pick(match)
	if (isEmail.value) {
		emit("select", { email: query.value.trim(), full_name: "" })
		query.value = ""
	}
}

function closeSoon() {
	setTimeout(() => (open.value = false), 150)
}
</script>
