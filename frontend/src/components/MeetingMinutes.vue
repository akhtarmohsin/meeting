<template>
	<div class="space-y-4">
		<div>
			<div class="mb-2 text-sm text-ink-gray-6">Minutes</div>
			<!-- Editor renders no element of its own, so the frame is this wrapper. -->
			<div class="rounded-6 border border-outline-gray-2">
				<Editor
					v-model="minutes"
					:extensions="[RichTextKit]"
					:editable="canEdit"
					placeholder="Capture what was discussed…"
				>
					<template #default="{ editor }">
						<EditorFixedMenu
							v-if="canEdit"
							:editor
							:items="commentToolbar"
							class="border-b border-outline-gray-2 px-2 py-1"
						/>
						<EditorContent
							:editor
							class="prose prose-sm min-h-[12rem] max-w-none px-3 py-2"
						/>
					</template>
				</Editor>
			</div>
		</div>
		<FormControl
			v-model="decisions"
			type="textarea"
			label="Decisions"
			:rows="3"
			:disabled="!canEdit"
			placeholder="One decision per line"
		/>
		<div v-if="canEdit" class="flex justify-end">
			<Button variant="solid" :loading="saving" :disabled="!dirty" @click="submit"
				>Save minutes</Button
			>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { Button, FormControl } from "frappe-ui";
import {
	Editor,
	EditorContent,
	EditorFixedMenu,
	RichTextKit,
	commentToolbar,
} from "frappe-ui/editor";

const props = defineProps({ doc: Object, canEdit: Boolean, save: Function });

const minutes = ref(props.doc.minutes || "");
const decisions = ref(props.doc.decisions || "");
const saving = ref(false);

const dirty = computed(
	() =>
		minutes.value !== (props.doc.minutes || "") ||
		decisions.value !== (props.doc.decisions || "")
);

async function submit() {
	saving.value = true;
	try {
		await props.save({ minutes: minutes.value, decisions: decisions.value });
	} finally {
		saving.value = false;
	}
}
</script>
