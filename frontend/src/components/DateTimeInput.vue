<template>
	<div class="flex flex-col gap-1.5">
		<span v-if="label" class="text-sm text-ink-gray-6">{{ label }}</span>
		<!-- The same pair of controls as Frappe Calendar's event form, at its 7:6 split. -->
		<div class="flex gap-2">
			<FormControl
				:model-value="date"
				type="date"
				format="MMM D, YYYY"
				placeholder="Select date"
				class="min-w-0 flex-[7]"
				@update:model-value="setDate"
			/>
			<FormControl
				:model-value="time"
				type="time"
				:interval="15"
				format="h:mm A"
				placeholder="Select time"
				class="min-w-0 flex-[6]"
				@update:model-value="setTime"
			/>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import dayjs from "dayjs";
import { FormControl } from "frappe-ui";

// Frappe's "YYYY-MM-DD HH:mm:ss".
const props = defineProps({ modelValue: String, label: String });
const emit = defineEmits(["update:modelValue"]);

const date = computed(() =>
	props.modelValue ? dayjs(props.modelValue).format("YYYY-MM-DD") : ""
);
const time = computed(() => (props.modelValue ? dayjs(props.modelValue).format("HH:mm") : ""));

function setDate(value) {
	if (value) emit("update:modelValue", `${value} ${time.value || "09:00"}:00`);
}

function setTime(value) {
	if (value)
		emit(
			"update:modelValue",
			`${date.value || dayjs().format("YYYY-MM-DD")} ${value.slice(0, 5)}:00`
		);
}
</script>
