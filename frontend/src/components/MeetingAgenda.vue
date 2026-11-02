<template>
	<div class="flex flex-col gap-2">
		<EmptyState v-if="!doc.agenda.length" icon="list" title="No agenda for this meeting" />
		<template v-else>
			<p class="text-sm text-ink-gray-6">
				{{ discussedCount }} of {{ doc.agenda.length }} discussed · {{ totalMinutes }} min planned
			</p>
			<div class="flex flex-col divide-y divide-outline-gray-1">
				<label
					v-for="(item, i) in doc.agenda"
					:key="item.name"
					class="flex items-start gap-3 py-3"
					:class="{ 'cursor-pointer': canEdit }"
				>
					<input
						type="checkbox"
						class="mt-0.5 shrink-0"
						:checked="item.discussed"
						:disabled="!canEdit"
						@change="toggleDiscussed(item, $event.target.checked)"
					/>
					<span class="w-5 shrink-0 text-base tabular-nums text-ink-gray-5">{{ i + 1 }}.</span>
					<div class="flex min-w-0 flex-1 flex-col gap-1">
						<span
							class="text-base font-medium"
							:class="item.discussed ? 'text-ink-gray-5 line-through' : 'text-ink-gray-9'"
						>
							{{ item.topic }}
						</span>
						<span v-if="item.notes" class="whitespace-pre-line text-sm leading-relaxed text-ink-gray-7">
							{{ item.notes }}
						</span>
					</div>
					<span class="w-14 shrink-0 text-right text-sm tabular-nums text-ink-gray-6">
						{{ item.duration ? `${item.duration} min` : "" }}
					</span>
				</label>
			</div>
		</template>
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
