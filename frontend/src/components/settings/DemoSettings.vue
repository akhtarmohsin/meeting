<template>
	<SettingsHeader
		title="Demo data"
		description="Fill Meeting with sample people, groups, meetings and action items"
	/>
	<SettingsBody>
		<div class="flex flex-col gap-6 pt-6">
			<p class="max-w-xl text-p-base text-ink-gray-7">
				Adds 13 sample people and 4 User Groups, then a set of meetings around you:
				finished meetings with minutes, an invite awaiting your reply, a repeating standup
				and more. Dates are relative to today. No email is sent.
			</p>
			<SettingsRow
				title="Start fresh"
				description="Delete every meeting and action item on this site first"
			>
				<Switch v-model="reset" />
			</SettingsRow>
			<div>
				<Button variant="solid" :loading="demo.loading" @click="load">
					Load demo data
				</Button>
			</div>
			<p v-if="demo.data" class="text-base text-ink-gray-7">{{ demo.data }}</p>
			<p v-if="demo.error" class="text-base text-ink-red-8">
				{{ errorMessage(demo.error) }}
			</p>
		</div>
	</SettingsBody>
</template>

<script setup>
import { ref } from "vue";
import {
	Button,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
	Switch,
	createResource,
	dialog,
	toast,
} from "frappe-ui";
import { errorMessage } from "@/utils";

const reset = ref(false);

const demo = createResource({
	url: "meeting.api.demo.load_demo",
	onSuccess: () => {
		toast.success("Demo data loaded");
		// Every page reads its data on load, so a reload shows the demo everywhere.
		setTimeout(() => window.location.reload(), 1200);
	},
});

function load() {
	if (!reset.value) return demo.submit({ reset: false });
	dialog.danger({
		title: "Delete all meetings?",
		message:
			"Every meeting and action item on this site will be deleted before the demo is loaded.",
		confirmLabel: "Delete and load demo",
		onConfirm: () => demo.submit({ reset: true }),
	});
}
</script>
