<template>
	<div class="flex flex-col items-center gap-3 py-12 text-center">
		<Icon :name="icon" class="h-5 w-5 text-ink-gray-4" />
		<p class="text-base text-ink-gray-6">{{ title }}</p>
		<Button v-if="action" variant="ghost" :route="to" @click="$emit('action')">
			<template #prefix><Icon name="lucide-plus" class="h-4 w-4" /></template>
			{{ action }}
		</Button>
	</div>
</template>

<script setup>
import { Button, Icon } from "frappe-ui"

defineProps({
	icon: { type: String, default: "lucide-inbox" },
	title: String,
	action: String,
	to: Object,
})
defineEmits(["action"])
</script>
