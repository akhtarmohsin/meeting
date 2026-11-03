<template>
	<div>
		<div v-if="meeting" class="flex justify-end pb-2">
			<Button @click="edit(null)">
				<template #prefix><Icon name="lucide-plus" class="h-4 w-4" /></template>
				Add action item
			</Button>
		</div>
		<EmptyState v-if="!items.length" icon="lucide-square-check-big" :title="emptyText" />
		<div v-else class="flex flex-col">
			<div
				v-for="item in items"
				:key="item.name"
				class="-mx-3 flex cursor-pointer items-center gap-3 rounded-5 px-3 py-3 hover:bg-surface-gray-1"
				@click="edit(item)"
			>
				<Checkbox
					class="shrink-0"
					:model-value="item.status === 'Done'"
					@click.stop
					@update:model-value="(checked) => toggleDone(item, checked)"
				/>
				<div class="min-w-0 flex-1">
					<div
						class="truncate text-base-medium"
						:class="item.status === 'Done' ? 'text-ink-gray-5 line-through' : 'text-ink-gray-9'"
					>
						{{ item.title }}
					</div>
					<div class="mt-1 flex items-center gap-1.5 truncate text-sm text-ink-gray-6">
						<router-link
							v-if="showMeeting && item.meeting"
							:to="{ name: 'Meeting', params: { name: item.meeting } }"
							class="truncate hover:text-ink-gray-8 hover:underline"
							@click.stop
						>
							{{ item.meeting_title || item.meeting }}
						</router-link>
						<span v-if="showMeeting && item.meeting && item.due_date">·</span>
						<span v-if="item.due_date" class="shrink-0" :class="{ 'font-medium text-ink-red-8': isOverdue(item) }">
							{{ isOverdue(item) ? "Overdue" : "Due" }} {{ formatDate(item.due_date, "D MMM") }}
						</span>
					</div>
				</div>
				<!-- Fixed lanes keep priority, status and assignee aligned across rows. -->
				<div class="hidden w-12 shrink-0 justify-end sm:flex">
					<span v-if="item.priority === 'High'" class="text-sm-medium text-ink-red-8">High</span>
				</div>
				<div class="flex w-24 shrink-0 justify-end">
					<Badge :label="item.status" :theme="ACTION_STATUS_THEME[item.status]" />
				</div>
				<div class="flex w-6 shrink-0 justify-end">
					<Avatar v-if="item.assigned_to" :label="item.assigned_to" size="sm" />
				</div>
			</div>
		</div>
		<ActionItemDialog v-model="dialog" :item="selected" :meeting="meeting" :people="people" @saved="$emit('changed')" />
	</div>
</template>

<script setup>
import { ref } from "vue"
import { Avatar, Badge, Button, Checkbox, Icon, call } from "frappe-ui"
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
