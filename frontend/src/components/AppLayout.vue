<template>
	<div class="flex h-screen overflow-hidden bg-surface-base">
		<!-- frappe-ui's sidebar, as Frappe Drive and the other Suite apps use it. -->
		<Sidebar v-model:collapsed="collapsed" class="hidden sm:flex">
			<SidebarHeader title="Meeting" :subtitle="session.fullName" :logo="logo" :menu-items="menuItems" />
			<div class="flex-1 overflow-y-auto px-2">
				<SidebarSection>
					<SidebarItem
						v-for="link in links"
						:key="link.label"
						:label="link.label"
						:icon="link.icon"
						:route="link.to"
						:active="isActive(link)"
					/>
				</SidebarSection>
			</div>
			<div class="p-2">
				<SidebarItem label="New Meeting" icon="lucide-plus" :route="{ name: 'NewMeeting' }" :active="false" />
				<SidebarCollapseToggle />
			</div>
		</Sidebar>

		<div class="flex min-w-0 flex-1 flex-col">
			<main class="flex-1 overflow-y-auto pb-14 sm:pb-0">
				<router-view :key="$route.fullPath" />
			</main>
			<nav class="fixed inset-x-0 bottom-0 flex h-14 border-t bg-surface-base sm:hidden">
				<router-link
					v-for="link in links"
					:key="link.label"
					:to="link.to"
					class="flex flex-1 flex-col items-center justify-center gap-0.5 text-xs text-ink-gray-6"
					exact-active-class="!text-ink-gray-9"
				>
					<Icon :name="link.icon" class="h-5 w-5" />
					{{ link.label }}
				</router-link>
				<router-link
					:to="{ name: 'NewMeeting' }"
					class="flex flex-1 flex-col items-center justify-center gap-0.5 text-xs text-ink-gray-6"
				>
					<Icon name="lucide-circle-plus" class="h-5 w-5" />
					New
				</router-link>
			</nav>
		</div>
	</div>
</template>

<script setup>
import { computed, h, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import {
	Icon,
	Sidebar,
	SidebarCollapseToggle,
	SidebarHeader,
	SidebarItem,
	SidebarSection,
	createResource,
	useColorScheme,
} from "frappe-ui"
import { session } from "@/data/session"

const logo = "/assets/meeting/images/logo.svg"
const DOCS_URL = "https://docs.frappe.io"
const SUPPORT_URL = "https://discuss.frappe.io"

const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const { colorScheme, setColorScheme } = useColorScheme()

const links = [
	{ label: "Home", icon: "lucide-house", to: { name: "Home" } },
	{ label: "Meetings", icon: "lucide-calendar", to: { name: "Meetings" } },
	{ label: "Action Items", icon: "lucide-square-check-big", to: { name: "ActionItems" } },
]

// The apps this user can open, from the same list as Frappe's /apps page.
const apps = createResource({ url: "frappe.apps.get_apps", auto: true })

// Grouped like Frappe Drive's menu: switching and help first, account last.
const menuItems = computed(() => [
	{
		group: "Manage",
		hideLabel: true,
		options: [
			{ label: "Apps", icon: "lucide-layout-grid", submenu: appItems.value },
			{ label: "Documentation", icon: "lucide-book", onClick: () => window.open(DOCS_URL, "_blank") },
			{ label: "Support", icon: "lucide-badge-help", onClick: () => window.open(SUPPORT_URL, "_blank") },
			{
				label: "Theme",
				icon: "lucide-sun-moon",
				submenu: [
					themeOption("Light", "light", "lucide-sun"),
					themeOption("Dark", "dark", "lucide-moon"),
					themeOption("Automatic", "system", "lucide-monitor"),
				],
			},
		],
	},
	{
		group: "Others",
		hideLabel: true,
		options: [
			{ label: "Settings", icon: "lucide-settings", onClick: () => (window.location.href = `/desk/user/${session.user}`) },
			{ label: "Log out", icon: "lucide-log-out", onClick: () => session.logout() },
		],
	},
])

const appItems = computed(() => {
	const items = (apps.data || [])
		.filter((app) => app.name !== "meeting")
		.map((app) => ({
			label: app.title,
			icon: h("img", { src: app.logo, class: "!size-6" }),
			onClick: () => (window.location.href = app.route),
		}))
	return [...items, { label: "Desk", icon: "lucide-monitor", onClick: () => (window.location.href = "/desk") }]
})

function themeOption(label, scheme, icon) {
	// A tick marks the active choice, as in Drive.
	return { label, icon: colorScheme.value === scheme ? "lucide-check" : icon, onClick: () => setColorScheme(scheme) }
}

function isActive(link) {
	const path = router.resolve(link.to).path
	return path === "/meeting" ? route.path === path : route.path.startsWith(path)
}
</script>
