import dayjs from "dayjs"

export const MEETING_STATUS_THEME = {
	Scheduled: "blue",
	"In Progress": "orange",
	Completed: "green",
	Cancelled: "gray",
}

export const RSVP_THEME = {
	Accepted: "green",
	Declined: "red",
	Tentative: "orange",
	Pending: "gray",
}

export const ACTION_STATUS_THEME = {
	Open: "blue",
	"In Progress": "orange",
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

// Frappe stores "YYYY-MM-DD HH:mm:ss"; <input type="datetime-local"> wants "YYYY-MM-DDTHH:mm".
export function toInputDatetime(value) {
	return value ? dayjs(value).format("YYYY-MM-DDTHH:mm") : ""
}

export function fromInputDatetime(value) {
	return value ? dayjs(value).format("YYYY-MM-DD HH:mm:ss") : null
}

export function errorMessage(error) {
	const messages = error?.messages || []
	return messages.length ? messages.join("\n") : error?.message || "Something went wrong"
}
