<template>
	<div>
		<EmptyState v-if="!doc.agenda.length" icon="list" title="No agenda for this meeting" />
		<div v-else class="divide-y rounded-lg border">
			<div v-for="(item, i) in doc.agenda" :key="item.name" class="flex items-start gap-3 px-4 py-3">
				<input
					type="checkbox"
					class="mt-1"
					:checked="item.discussed"
					:disabled="!canEdit"
					@change="toggleDiscussed(item, $event.target.checked)"
				/>
				<div class="min-w-0 flex-1">
					<div class="text-base text-ink-gray-9" :class="{ 'line-through text-ink-gray-5': item.discussed }">
						{{ i + 1 }}. {{ item.topic }}
					</div>
					<div v-if="item.notes" class="mt-1 whitespace-pre-line text-sm text-ink-gray-6">{{ item.notes }}</div>
				</div>
				<span v-if="item.duration" class="shrink-0 text-sm text-ink-gray-5">{{ item.duration }} min</span>
			</div>
		</div>
		<div v-if="doc.agenda.length" class="mt-2 text-sm text-ink-gray-5">
			{{ discussedCount }} of {{ doc.agenda.length }} discussed · {{ totalMinutes }} min planned
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"
import EmptyState from "@/components/EmptyState.vue"

const props = defineProps({ doc: Object, canEdit: Boolean, save: Function })

const discussedCount = computed(() => props.doc.agenda.filter((i) => i.discussed).length)
const totalMinutes = computed(() => props.doc.agenda.reduce((sum, i) => sum + (i.duration || 0), 0))

function toggleDiscussed(item, checked) {
	const agenda = props.doc.agenda.map((i) => (i.name === item.name ? { ...i, discussed: checked ? 1 : 0 } : i))
	props.save({ agenda })
}
</script>
