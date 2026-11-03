<template>
	<div class="flex flex-col gap-2">
		<div v-if="canEdit" class="flex justify-end pb-2">
			<Button @click="edit(null)">
				<template #prefix><Icon name="lucide-plus" class="h-4 w-4" /></template>
				Add agenda item
			</Button>
		</div>
		<EmptyState
			v-if="!doc.agenda.length"
			icon="lucide-list"
			title="No agenda for this meeting"
		/>
		<template v-else>
			<p class="text-sm text-ink-gray-6">
				{{ discussedCount }} of {{ doc.agenda.length }} discussed · {{ totalMinutes }} min
				planned
			</p>
			<div class="flex flex-col divide-y divide-outline-gray-1">
				<div
					v-for="(item, i) in doc.agenda"
					:key="item.name"
					class="flex items-start gap-3 py-3"
					:class="{ 'cursor-pointer': canEdit }"
					@click="canEdit && edit(item)"
				>
					<Checkbox
						class="mt-0.5 shrink-0"
						:model-value="Boolean(item.discussed)"
						:disabled="!canEdit"
						@click.stop
						@update:model-value="(checked) => toggleDiscussed(item, checked)"
					/>
					<span class="w-5 shrink-0 text-base tabular-nums text-ink-gray-5"
						>{{ i + 1 }}.</span
					>
					<div class="flex min-w-0 flex-1 flex-col gap-1">
						<span
							class="text-base-medium"
							:class="
								item.discussed ? 'text-ink-gray-5 line-through' : 'text-ink-gray-9'
							"
						>
							{{ item.topic }}
						</span>
						<span
							v-if="item.notes"
							class="whitespace-pre-line text-sm leading-relaxed text-ink-gray-7"
						>
							{{ item.notes }}
						</span>
					</div>
					<div
						class="flex w-52 shrink-0 flex-col items-end gap-1 text-right text-sm text-ink-gray-6"
					>
						<span class="tabular-nums">{{
							item.duration ? `${item.duration} min` : ""
						}}</span>
						<span v-if="item.presenter" class="max-w-full truncate">
							Presented by {{ presenterName(item.presenter) }}
						</span>
					</div>
				</div>
			</div>
		</template>
		<AgendaItemDialog
			v-model="dialog"
			:item="selected"
			:people="doc.attendees"
			:on-submit="saveItem"
			:on-remove="removeItem"
		/>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { Button, Checkbox, Icon } from "frappe-ui";
import AgendaItemDialog from "@/components/AgendaItemDialog.vue";
import EmptyState from "@/components/EmptyState.vue";

const props = defineProps({ doc: Object, canEdit: Boolean, save: Function });

const dialog = ref(false);
const selected = ref(null);

const discussedCount = computed(() => props.doc.agenda.filter((i) => i.discussed).length);
const totalMinutes = computed(() =>
	props.doc.agenda.reduce((sum, i) => sum + (i.duration || 0), 0)
);

function edit(item) {
	selected.value = item;
	dialog.value = true;
}

function presenterName(user) {
	const person = props.doc.attendees.find((a) => a.user === user);
	return person?.full_name || user;
}

// The agenda is a child table, so every change saves the whole list.
function saveItem(values) {
	const agenda = selected.value
		? props.doc.agenda.map((i) => (i.name === selected.value.name ? { ...i, ...values } : i))
		: [...props.doc.agenda, { ...values, discussed: 0 }];
	return props.save({ agenda });
}

function removeItem() {
	return props.save({ agenda: props.doc.agenda.filter((i) => i.name !== selected.value.name) });
}

function toggleDiscussed(item, checked) {
	const agenda = props.doc.agenda.map((i) =>
		i.name === item.name ? { ...i, discussed: checked ? 1 : 0 } : i
	);
	props.save({ agenda });
}
</script>
