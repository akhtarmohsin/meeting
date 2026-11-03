<template>
	<div class="relative">
		<TextInput
			v-model="query"
			:placeholder="placeholder"
			@focus="open = true"
			@click="open = true"
			@blur="closeSoon"
			@keydown.enter.prevent="pickTyped"
		>
			<template #prefix><Icon name="lucide-search" class="h-4 w-4" /></template>
		</TextInput>
		<div
			v-if="open && (groups.data?.length || results.data?.length || isEmail)"
			class="absolute z-20 mt-1 max-h-60 w-full overflow-y-auto rounded-6 border bg-surface-base p-1 shadow-lg"
		>
			<template v-if="groups.data?.length">
				<div class="px-2 pb-1 pt-1.5 text-xs text-ink-gray-5">Groups</div>
				<button
					v-for="g in groups.data"
					:key="g.name"
					class="flex w-full items-center gap-2 rounded-4 px-2 py-1.5 text-left hover:bg-surface-gray-2"
					@mousedown.prevent="pickGroup(g)"
				>
					<span class="flex size-5 shrink-0 items-center justify-center rounded-full bg-surface-gray-3">
						<Icon name="lucide-users" class="size-3 text-ink-gray-6" />
					</span>
					<div class="min-w-0">
						<div class="truncate text-base text-ink-gray-9">{{ g.name }}</div>
						<div class="truncate text-sm text-ink-gray-6">
							{{ g.member_count }} {{ g.member_count === 1 ? "member" : "members" }}
						</div>
					</div>
				</button>
				<div v-if="results.data?.length" class="px-2 pb-1 pt-2 text-xs text-ink-gray-5">People</div>
			</template>
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
// "select" adds one person; "select-group" hands over a User Group name to add its members.
const emit = defineEmits(["select", "select-group"])

const query = ref("")
const open = ref(false)

const results = createResource({
	url: "meeting.api.meetings.search_users",
	makeParams: () => ({ txt: query.value }),
	auto: true,
})

const groups = createResource({
	url: "meeting.api.meetings.search_user_groups",
	makeParams: () => ({ txt: query.value }),
	auto: true,
})

watch(
	query,
	debounce(() => {
		results.reload()
		groups.reload()
	}, 250),
)

const isEmail = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(query.value.trim()))

function pick(user) {
	emit("select", { user: user.name, email: user.email, full_name: user.full_name })
	done()
}

function pickGroup(group) {
	emit("select-group", group.name)
	done()
}

function pickTyped() {
	const match = results.data?.[0]
	if (match && !isEmail.value) return pick(match)
	if (isEmail.value) {
		emit("select", { email: query.value.trim(), full_name: "" })
		done()
	}
}

// Close the list after a pick so the attendee just added is in view.
function done() {
	query.value = ""
	open.value = false
}

function closeSoon() {
	setTimeout(() => (open.value = false), 150)
}
</script>
