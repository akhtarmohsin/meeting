import dayjs from "dayjs"

export const MEETING_STATUS_THEME = {
	Scheduled: "blue",
	"In Progress": "amber",
	Completed: "green",
	Cancelled: "gray",
}

export const RSVP_THEME = {
	Accepted: "green",
	Declined: "red",
	Tentative: "amber",
	Pending: "gray",
}

export const ACTION_STATUS_THEME = {
	Open: "blue",
	"In Progress": "amber",
	Done: "green",
	Cancelled: "gray",
}

export const PRIORITY_THEME = { Low: "gray", Medium: "blue", High: "red" }

export function formatTime(value) {
	return dayjs(value).format("h:mm A")
}

export function formatDate(value, format = "ddd, D MMM YYYY") {
	return value ? dayjs(value).format(format) : ""
}

export function formatRange(start, end) {
	return `${formatTime(start)} – ${formatTime(end)}`
}

export function dayLabel(value) {
	const day = dayjs(value).startOf("day")
	const today = dayjs().startOf("day")
	if (day.isSame(today)) return "Today"
	if (day.isSame(today.add(1, "day"))) return "Tomorrow"
	if (day.isSame(today.subtract(1, "day"))) return "Yesterday"
	return day.format("dddd, D MMM YYYY")
}

export function groupByDay(meetings) {
	const groups = []
	for (const m of meetings) {
		const label = dayLabel(m.start)
		const last = groups[groups.length - 1]
		if (last?.label === label) last.meetings.push(m)
		else groups.push({ label, meetings: [m] })
	}
	return groups
}

export function isOverdue(item) {
	return item.due_date && !["Done", "Cancelled"].includes(item.status) && dayjs(item.due_date).isBefore(dayjs(), "day")
}

export function fromInputDatetime(value) {
	return value ? dayjs(value).format("YYYY-MM-DD HH:mm:ss") : null
}

export function errorMessage(error) {
	const messages = error?.messages || []
	return messages.length ? messages.join("\n") : error?.message || "Something went wrong"
}

const REPEAT_UNITS = { daily: "day", weekly: "week", monthly: "month", yearly: "year" }
const DAY_NAMES = { mo: "Mon", tu: "Tue", we: "Wed", th: "Thu", fr: "Fri", sa: "Sat", su: "Sun" }
const ORDINALS = { 1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth", "-1": "Last" }

// Worded like Frappe Calendar's repeat summary.
export function repeatMessage(rule) {
	const unit = REPEAT_UNITS[rule?.frequency]
	if (!unit) return ""
	const interval = rule.interval || 1
	let message = interval === 1 ? `Every ${unit}` : `Every ${interval} ${unit}s`
	if (rule.byDay?.length) {
		const days = rule.byDay.map((d) => (d.nthOfPeriod ? `${ORDINALS[d.nthOfPeriod]} ${DAY_NAMES[d.day]}` : DAY_NAMES[d.day]))
		message += ` on ${days.join(", ")}`
	} else if (rule.byMonthDay?.length) {
		const day = rule.byMonthDay[0]
		message += day === -1 ? " on the last day" : ` on day ${day}`
	}
	if (rule.until) return `${message} until ${dayjs(rule.until.replace(/Z$/, "")).format("MMM DD, YYYY")}`
	if (rule.count) return `${message}, ${rule.count} times`
	return message
}
