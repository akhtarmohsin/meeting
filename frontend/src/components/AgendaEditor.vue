<template>
	<section>
		<div class="mb-2 flex items-center justify-between">
			<span class="text-sm text-ink-gray-5">
				Agenda <span v-if="totalMinutes">· {{ totalMinutes }} min</span>
			</span>
			<Button size="sm" variant="ghost" @click="add">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				Add item
			</Button>
		</div>
		<div v-if="items.length" class="divide-y rounded-lg border">
			<div v-for="(item, i) in items" :key="i" class="flex items-center gap-2 px-3 py-2">
				<span class="w-5 text-sm text-ink-gray-4">{{ i + 1 }}.</span>
				<TextInput v-model="item.topic" class="flex-1" placeholder="Topic" variant="ghost" />
				<TextInput
					v-model.number="item.duration"
					type="number"
					class="w-20"
					placeholder="min"
					variant="ghost"
				/>
				<Button variant="ghost" size="sm" @click="items.splice(i, 1)">
					<template #icon><FeatherIcon name="trash-2" class="h-4 w-4" /></template>
				</Button>
			</div>
		</div>
		<p v-else class="text-sm text-ink-gray-4">No agenda items yet.</p>
	</section>
</template>

<script setup>
import { computed } from "vue"
import { Button, FeatherIcon, TextInput } from "frappe-ui"

const items = defineModel({ type: Array, default: () => [] })

const totalMinutes = computed(() => items.value.reduce((sum, i) => sum + (Number(i.duration) || 0), 0))

function add() {
	items.value.push({ topic: "", duration: null, discussed: 0 })
}
</script>
