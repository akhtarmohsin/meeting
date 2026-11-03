<template>
	<component
		:is="to ? 'router-link' : 'div'"
		:to="to"
		class="flex flex-col gap-1.5 py-1 sm:px-6 sm:first:pl-0"
		:class="{ 'group': to }"
	>
		<span class="text-sm text-ink-gray-6 group-hover:text-ink-gray-8">{{ label }}</span>
		<span
			class="text-3xl-semibold leading-none tabular-nums"
			:class="danger ? 'text-ink-red-8' : 'text-ink-gray-9'"
		>
			{{ value ?? "–" }}
		</span>
	</component>
</template>

<script setup>
defineProps({
	label: String,
	value: Number,
	danger: Boolean,
	to: Object,
})
</script>
