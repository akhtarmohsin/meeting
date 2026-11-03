<template>
	<!-- Hosts frappe-ui's toasts and dialogs for the whole app. -->
	<FrappeUIProvider>
		<router-view />
	</FrappeUIProvider>
</template>

<script setup>
import { FrappeUIProvider } from "frappe-ui"
</script>
