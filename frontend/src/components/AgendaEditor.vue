<template>
	<section>
		<div class="mb-2 flex h-7 items-center justify-between">
			<span class="text-sm text-ink-gray-6">
				Agenda<span v-if="items.length"> · {{ items.length }}</span>
				<span v-if="totalMinutes">· {{ totalMinutes }} min</span>
			</span>
			<Button size="sm" variant="ghost" @click="add">
				<template #prefix><Icon name="lucide-plus" class="h-4 w-4" /></template>
				Add item
			</Button>
		</div>
		<!-- Same fixed, scrolling box as the attendee list beside it. -->
		<div
			v-if="items.length"
			ref="list"
			class="flex max-h-72 flex-col divide-y divide-outline-gray-1 overflow-y-auto rounded-6 border border-outline-gray-2 px-3"
		>
			<div v-for="(item, i) in items" :key="i" class="flex items-center gap-2 py-1.5">
				<span class="w-5 text-sm text-ink-gray-5">{{ i + 1 }}.</span>
				<TextInput v-model="item.topic" class="flex-1" placeholder="Topic" variant="ghost" />
				<TextInput
					v-model.number="item.duration"
					type="number"
					class="w-20"
					placeholder="min"
					variant="ghost"
				/>
				<Button variant="ghost" size="sm" @click="items.splice(i, 1)">
					<template #icon><Icon name="lucide-trash-2" class="h-4 w-4" /></template>
				</Button>
			</div>
		</div>
		<p v-else class="text-sm text-ink-gray-5">No agenda items yet.</p>
	</section>
</template>

<script setup>
import { computed, nextTick, ref } from "vue"
import { Button, Icon, TextInput } from "frappe-ui"

const items = defineModel({ type: Array, default: () => [] })

const totalMinutes = computed(() => items.value.reduce((sum, i) => sum + (Number(i.duration) || 0), 0))

const list = ref(null)

async function add() {
	items.value.push({ topic: "", duration: null, discussed: 0 })
	// The new row lands at the bottom of a scrolling box: bring it into view and start typing there.
	await nextTick()
	if (!list.value) return
	list.value.scrollTop = list.value.scrollHeight
	list.value.querySelector(":scope > div:last-child input")?.focus()
}
</script>
