<template>
	<div>
		<div v-if="meeting" class="mb-3 flex justify-end">
			<Button @click="edit(null)">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				Add action item
			</Button>
		</div>
		<EmptyState v-if="!items.length" icon="check-square" :title="emptyText" />
		<div v-else class="divide-y rounded-lg border">
			<div
				v-for="item in items"
				:key="item.name"
				class="flex cursor-pointer items-center gap-3 px-4 py-2.5 hover:bg-surface-gray-1"
				@click="edit(item)"
			>
				<input
					type="checkbox"
					:checked="item.status === 'Done'"
					@click.stop
					@change="toggleDone(item, $event.target.checked)"
				/>
				<div class="min-w-0 flex-1">
					<div class="truncate text-base text-ink-gray-9" :class="{ 'line-through text-ink-gray-5': item.status === 'Done' }">
						{{ item.title }}
					</div>
					<div class="mt-0.5 flex items-center gap-2 truncate text-sm text-ink-gray-5">
						<router-link
							v-if="showMeeting && item.meeting"
							:to="{ name: 'Meeting', params: { name: item.meeting } }"
							class="hover:underline"
							@click.stop
						>
							{{ item.meeting_title || item.meeting }}
						</router-link>
						<span v-if="item.due_date" :class="{ 'text-ink-red-4': isOverdue(item) }">
							Due {{ formatDate(item.due_date, "D MMM") }}
						</span>
					</div>
				</div>
				<Badge v-if="item.priority === 'High'" label="High" theme="red" />
				<Badge :label="item.status" :theme="ACTION_STATUS_THEME[item.status]" />
				<Avatar v-if="item.assigned_to" :label="item.assigned_to" size="sm" />
			</div>
		</div>
		<ActionItemDialog v-model="dialog" :item="selected" :meeting="meeting" :people="people" @saved="$emit('changed')" />
	</div>
</template>

<script setup>
import { ref } from "vue"
import { Avatar, Badge, Button, FeatherIcon, call } from "frappe-ui"
import ActionItemDialog from "@/components/ActionItemDialog.vue"
import EmptyState from "@/components/EmptyState.vue"
import { ACTION_STATUS_THEME, formatDate, isOverdue } from "@/utils"

defineProps({
	items: { type: Array, default: () => [] },
	meeting: String,
	people: { type: Array, default: () => [] },
	showMeeting: Boolean,
	emptyText: { type: String, default: "No action items yet" },
})
const emit = defineEmits(["changed"])

const dialog = ref(false)
const selected = ref(null)

function edit(item) {
	selected.value = item
	dialog.value = true
}

defineExpose({ edit })

async function toggleDone(item, done) {
	await call("meeting.api.action_items.set_status", { name: item.name, status: done ? "Done" : "Open" })
	emit("changed")
}
</script>
