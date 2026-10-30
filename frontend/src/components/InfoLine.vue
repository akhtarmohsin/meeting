<template>
	<div class="flex items-center gap-2">
		<FeatherIcon :name="icon" class="h-4 w-4 shrink-0 text-ink-gray-5" />
		<span class="truncate"><slot /></span>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"

defineProps({ icon: String })
</script>
