<template>
	<Dialog v-model:open="show" :title="item ? 'Edit agenda item' : 'New agenda item'">
		<template #default>
			<div class="flex flex-col gap-4">
				<FormControl
					v-model="form.topic"
					label="Topic"
					placeholder="Review Q4 hiring plan"
				/>
				<div class="grid grid-cols-2 gap-4">
					<FormControl
						v-model="form.presenter"
						type="select"
						label="Presenter"
						:options="presenterOptions"
					/>
					<FormControl
						v-model="form.duration"
						type="number"
						label="Duration (min)"
						placeholder="15"
					/>
				</div>
				<FormControl v-model="form.notes" type="textarea" label="Notes" :rows="3" />
				<ErrorMessage :message="error" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-between">
				<Button
					v-if="item"
					theme="red"
					variant="ghost"
					:loading="saving === 'remove'"
					@click="run('remove')"
				>
					Delete
				</Button>
				<div class="ml-auto flex gap-2">
					<Button @click="show = false">Cancel</Button>
					<Button variant="solid" :loading="saving === 'submit'" @click="submit"
						>Save</Button
					>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { Button, Dialog, ErrorMessage, FormControl } from "frappe-ui";
import { errorMessage } from "@/utils";

const show = defineModel({ type: Boolean });
const props = defineProps({
	item: Object,
	// Meeting attendees, offered as presenters.
	people: { type: Array, default: () => [] },
	// Async handlers from the parent; the dialog closes once they resolve.
	onSubmit: Function,
	onRemove: Function,
});

const form = reactive({});
const saving = ref(null);
const error = ref("");

const presenterOptions = computed(() => [
	{ label: "No presenter", value: "" },
	...props.people
		.filter((p) => p.user)
		.map((p) => ({ label: p.full_name || p.email, value: p.user })),
]);

watch(show, (open) => {
	if (!open) return;
	error.value = "";
	Object.assign(form, { topic: "", presenter: "", duration: null, notes: "", ...props.item });
});

function submit() {
	if (!form.topic?.trim()) {
		error.value = "Topic is required";
		return;
	}
	run("submit", { ...form, topic: form.topic.trim(), duration: Number(form.duration) || null });
}

async function run(action, values) {
	saving.value = action;
	error.value = "";
	try {
		await (action === "submit" ? props.onSubmit(values) : props.onRemove());
		show.value = false;
	} catch (e) {
		error.value = errorMessage(e);
	} finally {
		saving.value = null;
	}
}
</script>
