<template>
	<router-link
		:to="to"
		class="flex h-8 items-center gap-2 rounded px-2 text-base text-ink-gray-7 hover:bg-surface-gray-2"
		:class="{ 'bg-surface-selected text-ink-gray-9 shadow-sm': isActive }"
	>
		<FeatherIcon :name="icon" class="h-4 w-4" />
		{{ label }}
	</router-link>
</template>

<script setup>
import { computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { FeatherIcon } from "frappe-ui"

const props = defineProps({
	label: String,
	icon: String,
	to: Object,
})

const route = useRoute()
const router = useRouter()

const isActive = computed(() => {
	const path = router.resolve(props.to).path
	return path === "/meeting" ? route.path === path : route.path.startsWith(path)
})
</script>
