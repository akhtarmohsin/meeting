<template>
	<header class="page-header">
		<h1 class="text-lg-semibold text-ink-gray-9">Action Items</h1>
		<Button variant="solid" @click="list?.edit(null)">
			<template #prefix><Icon name="lucide-plus" class="h-4 w-4" /></template>
			New
		</Button>
	</header>
	<div class="page">
		<div class="mb-5 flex flex-wrap items-center gap-3">
			<TabButtons v-model="scope" :options="scopes" />
			<!-- The select fills its container in frappe-ui 1.0, so the width lives on a wrapper. -->
			<div class="w-40 sm:ml-auto">
				<FormControl v-model="status" type="select" :options="statuses" />
			</div>
		</div>
		<div v-if="items.error" class="text-base text-ink-red-8">
			{{ errorMessage(items.error) }}
		</div>
		<div v-else-if="items.loading && !items.data" class="text-base text-ink-gray-5">
			Loading…
		</div>
		<ActionItemList
			v-else
			ref="list"
			:items="items.data || []"
			show-meeting
			empty-text="You're all caught up"
			@changed="items.reload()"
		/>
	</div>
</template>

<script setup>
import { ref, watch } from "vue";
import { Button, FormControl, Icon, TabButtons, createResource } from "frappe-ui";
import ActionItemList from "@/components/ActionItemList.vue";
import { errorMessage } from "@/utils";

const scopes = [
	{ label: "Assigned to me", value: "mine" },
	{ label: "All", value: "all" },
];
const statuses = [
	{ label: "Pending", value: "pending" },
	{ label: "Done", value: "Done" },
	{ label: "Cancelled", value: "Cancelled" },
	{ label: "Any status", value: "" },
];
const scope = ref("mine");
const status = ref("pending");
const list = ref(null);

const items = createResource({
	url: "meeting.api.action_items.get_action_items",
	makeParams: () => ({ scope: scope.value, status: status.value || null }),
	auto: true,
});

watch([scope, status], () => items.reload());
</script>
