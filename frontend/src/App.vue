<template>
	<router-view />
	<Toasts />
	<Dialogs />
</template>

<script setup>
import { Toasts, Dialogs } from "frappe-ui"
</script>
