<template>
	<div class="flex flex-col items-center justify-center rounded-lg border border-dashed px-6 py-10 text-center">
		<FeatherIcon :name="icon" class="h-6 w-6 text-ink-gray-4" />
		<p class="mt-2 text-base text-ink-gray-6">{{ title }}</p>
		<Button v-if="action" class="mt-3" :route="to" @click="$emit('action')">{{ action }}</Button>
	</div>
</template>

<script setup>
import { Button, FeatherIcon } from "frappe-ui"

defineProps({
	icon: { type: String, default: "inbox" },
	title: String,
	action: String,
	to: Object,
})
defineEmits(["action"])
</script>
