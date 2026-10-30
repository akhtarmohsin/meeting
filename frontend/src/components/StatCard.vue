<template>
	<component
		:is="to ? 'router-link' : 'div'"
		:to="to"
		class="rounded-lg border p-4"
		:class="{ 'hover:bg-surface-gray-1': to }"
	>
		<div class="flex items-center justify-between text-sm text-ink-gray-5">
			{{ label }}
			<FeatherIcon :name="icon" class="h-4 w-4" />
		</div>
		<div class="mt-2 text-2xl font-semibold" :class="danger ? 'text-ink-red-4' : 'text-ink-gray-9'">
			{{ value ?? "–" }}
		</div>
	</component>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"

defineProps({
	label: String,
	value: Number,
	icon: String,
	danger: Boolean,
	to: Object,
})
</script>
