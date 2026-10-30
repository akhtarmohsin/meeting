<template>
	<div class="space-y-4">
		<div>
			<div class="mb-2 text-sm text-ink-gray-5">Minutes</div>
			<TextEditor
				:content="minutes"
				:editable="canEdit"
				:fixed-menu="canEdit"
				placeholder="Capture what was discussed…"
				editor-class="prose-sm max-w-none min-h-[12rem] px-3 py-2"
				class="rounded-lg border"
				@change="(v) => (minutes = v)"
			/>
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
			<Button variant="solid" :loading="saving" :disabled="!dirty" @click="submit">Save minutes</Button>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue"
import { Button, FormControl, TextEditor } from "frappe-ui"

const props = defineProps({ doc: Object, canEdit: Boolean, save: Function })

const minutes = ref(props.doc.minutes || "")
const decisions = ref(props.doc.decisions || "")
const saving = ref(false)

const dirty = computed(() => minutes.value !== (props.doc.minutes || "") || decisions.value !== (props.doc.decisions || ""))

async function submit() {
	saving.value = true
	try {
		await props.save({ minutes: minutes.value, decisions: decisions.value })
	} finally {
		saving.value = false
	}
}
</script>
