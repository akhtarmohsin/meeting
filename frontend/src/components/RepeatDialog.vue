<template>
	<Dialog v-model:open="show" :title="'Repeat'">
		<template #default>
			<div class="flex flex-col gap-4">
				<div class="flex flex-col gap-1.5">
					<span class="text-sm text-ink-gray-6">Repeat every</span>
					<div class="flex gap-2.5">
						<TextInput
							v-model.number="repeat.interval"
							type="number"
							min="1"
							class="w-16 shrink-0"
						/>
						<TabButtons
							v-model="repeat.frequency"
							:options="FREQUENCIES"
							fluid
							class="flex-1"
						/>
					</div>
				</div>

				<div v-if="repeat.frequency === 'weekly'" class="flex flex-col gap-1.5">
					<span class="text-sm text-ink-gray-6">On</span>
					<div class="flex gap-1.5">
						<button
							v-for="d in WEEKDAYS"
							:key="d.value"
							type="button"
							class="size-8 rounded-full text-sm transition-colors"
							:class="
								hasDay(d.value)
									? 'bg-surface-gray-10 text-ink-base'
									: 'bg-surface-gray-2 text-ink-gray-8 hover:bg-surface-gray-3'
							"
							:aria-pressed="hasDay(d.value)"
							@click="toggleDay(d.value)"
						>
							{{ d.label }}
						</button>
					</div>
				</div>

				<div v-else-if="repeat.frequency === 'monthly'" class="flex flex-col gap-1.5">
					<span class="text-sm text-ink-gray-6">On</span>
					<FormControl
						v-model="repeat.repeatOn"
						type="select"
						:options="monthlyOptions"
					/>
				</div>

				<div class="flex flex-col gap-1.5">
					<span class="text-sm text-ink-gray-6">Ends</span>
					<div class="grid grid-cols-2 gap-2.5">
						<FormControl v-model="repeat.end" type="select" :options="END_OPTIONS" />
						<FormControl
							v-if="repeat.end === 'until'"
							v-model="repeat.until"
							type="date"
						/>
						<TextInput
							v-else-if="repeat.end === 'count'"
							v-model.number="repeat.count"
							type="number"
							min="2"
						/>
					</div>
					<p v-if="repeat.end === 'never'" class="text-sm text-ink-gray-6">
						Meetings are created 3 months ahead and topped up daily.
					</p>
				</div>

				<div
					class="flex items-start gap-2.5 border-t border-outline-gray-1 pt-3 text-base text-ink-gray-8"
				>
					<Icon name="lucide-repeat" class="mt-0.5 h-4 w-4 shrink-0 text-ink-gray-5" />
					<span class="min-w-0 flex-1 leading-relaxed">{{ repeatMessage(rule) }}</span>
				</div>
				<ErrorMessage :message="error" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="remove">Remove repeat</Button>
				<Button variant="solid" @click="apply">Apply</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import dayjs from "dayjs";
import { Button, Dialog, ErrorMessage, FormControl, Icon, TabButtons, TextInput } from "frappe-ui";
import { repeatMessage } from "@/utils";

const show = defineModel({ type: Boolean });
const props = defineProps({
	// Meeting start, "YYYY-MM-DD HH:mm:ss"; weekday and day-of-month defaults come from it.
	start: String,
	value: Object,
});
const emit = defineEmits(["update"]);

const FREQUENCIES = [
	{ label: "Day", value: "daily" },
	{ label: "Week", value: "weekly" },
	{ label: "Month", value: "monthly" },
	{ label: "Year", value: "yearly" },
];
const WEEKDAYS = [
	{ label: "Su", value: "su" },
	{ label: "Mo", value: "mo" },
	{ label: "Tu", value: "tu" },
	{ label: "We", value: "we" },
	{ label: "Th", value: "th" },
	{ label: "Fr", value: "fr" },
	{ label: "Sa", value: "sa" },
];
const END_OPTIONS = [
	{ label: "Never", value: "never" },
	{ label: "On date", value: "until" },
	{ label: "After occurrences", value: "count" },
];
const ORDINALS = ["First", "Second", "Third", "Fourth", "Fifth"];

const repeat = reactive({});
const error = ref("");

const startDay = computed(() => dayjs(props.start).format("dd").toLowerCase());
const weekOfMonth = computed(() => Math.ceil(dayjs(props.start).date() / 7));

const monthlyOptions = computed(() => {
	const date = dayjs(props.start);
	const options = [{ label: `Day ${date.date()} of the month`, value: "day_of_month" }];
	if (date.date() === date.daysInMonth())
		options.push({ label: "Last day of the month", value: "last_day_of_month" });
	options.push({
		label: `${ORDINALS[weekOfMonth.value - 1]} ${date.format("dddd")}`,
		value: "day_of_week",
	});
	if (date.daysInMonth() - date.date() < 7)
		options.push({ label: `Last ${date.format("dddd")}`, value: "last_day_of_week" });
	return options;
});

// The rule in Frappe Calendar's shape, as the server stores it.
const rule = computed(() => {
	const result = {
		frequency: repeat.frequency,
		interval: Math.max(Number(repeat.interval) || 1, 1),
	};
	if (repeat.frequency === "weekly" && repeat.byDay?.length) {
		result.byDay = repeat.byDay;
	} else if (repeat.frequency === "monthly") {
		const date = dayjs(props.start);
		result.byDay = {
			day_of_week: [{ day: startDay.value, nthOfPeriod: weekOfMonth.value }],
			last_day_of_week: [{ day: startDay.value, nthOfPeriod: -1 }],
		}[repeat.repeatOn];
		result.byMonthDay = { day_of_month: [date.date()], last_day_of_month: [-1] }[
			repeat.repeatOn
		];
		if (!result.byDay) delete result.byDay;
		if (!result.byMonthDay) delete result.byMonthDay;
	}
	if (repeat.end === "until") result.until = `${repeat.until}T23:59:59`;
	else if (repeat.end === "count") result.count = Number(repeat.count);
	return result;
});

watch(show, (open) => {
	if (open) {
		error.value = "";
		Object.assign(repeat, fromRule(props.value));
	}
});

watch(
	() => repeat.frequency,
	(frequency) => {
		if (frequency === "weekly" && !repeat.byDay?.length)
			repeat.byDay = [{ day: startDay.value }];
	}
);

function hasDay(day) {
	return repeat.byDay?.some((d) => d.day === day);
}

function toggleDay(day) {
	repeat.byDay = hasDay(day)
		? repeat.byDay.filter((d) => d.day !== day)
		: [...(repeat.byDay || []), { day }];
}

function apply() {
	if (repeat.end === "until" && !dayjs(repeat.until).isAfter(dayjs(props.start), "day")) {
		error.value = "The end date must be after the meeting's start";
		return;
	}
	if (repeat.end === "count" && !(Number(repeat.count) >= 2)) {
		error.value = "A repeating meeting needs at least 2 occurrences";
		return;
	}
	emit("update", rule.value);
	show.value = false;
}

function remove() {
	emit("update", null);
	show.value = false;
}

function fromRule(value) {
	const defaults = {
		frequency: "weekly",
		interval: 1,
		byDay: [{ day: startDay.value }],
		repeatOn: "day_of_month",
		end: "count",
		until: dayjs(props.start).add(1, "month").format("YYYY-MM-DD"),
		count: 10,
	};
	if (!value?.frequency) return defaults;
	const byMonthDay = value.byMonthDay?.[0];
	const nth = value.byDay?.[0]?.nthOfPeriod;
	return {
		...defaults,
		frequency: value.frequency,
		interval: value.interval || 1,
		byDay: value.frequency === "weekly" ? value.byDay || defaults.byDay : defaults.byDay,
		repeatOn:
			byMonthDay === -1
				? "last_day_of_month"
				: nth === -1
				? "last_day_of_week"
				: nth
				? "day_of_week"
				: "day_of_month",
		end: value.until ? "until" : value.count ? "count" : "never",
		until: value.until
			? dayjs(value.until.replace(/Z$/, "")).format("YYYY-MM-DD")
			: defaults.until,
		count: value.count || defaults.count,
	};
}
</script>
