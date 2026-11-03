<template>
	<div class="flex h-screen overflow-hidden bg-surface-base">
		<aside class="hidden w-56 shrink-0 flex-col border-r bg-surface-sidebar sm:flex">
			<Dropdown :options="userMenu" class="p-2">
				<template #default="{ open }">
					<button
						class="flex w-full items-center gap-2 rounded-5 px-2 py-2 text-left hover:bg-surface-gray-3"
						:class="{ 'bg-surface-gray-3': open }"
					>
						<img :src="logo" class="h-8 w-8 rounded-5" />
						<div class="min-w-0 flex-1">
							<div class="text-base-medium text-ink-gray-9">Meeting</div>
							<div class="truncate text-sm text-ink-gray-6">{{ session.fullName }}</div>
						</div>
						<Icon name="lucide-chevron-down" class="h-4 w-4 text-ink-gray-5" />
					</button>
				</template>
			</Dropdown>

			<nav class="flex-1 space-y-0.5 px-2 py-2">
				<SidebarLink v-for="link in links" :key="link.label" v-bind="link" />
			</nav>

			<div class="p-2">
				<Button variant="subtle" class="w-full" :route="{ name: 'NewMeeting' }">
					<template #prefix><Icon name="lucide-plus" class="h-4 w-4" /></template>
					New Meeting
				</Button>
			</div>
		</aside>

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
import { Button, Dropdown, Icon } from "frappe-ui"
import SidebarLink from "@/components/SidebarLink.vue"
import { session } from "@/data/session"

const logo = "/assets/meeting/images/logo.svg"

const links = [
	{ label: "Home", icon: "lucide-house", to: { name: "Home" } },
	{ label: "Meetings", icon: "lucide-calendar", to: { name: "Meetings" } },
	{ label: "Action Items", icon: "lucide-square-check-big", to: { name: "ActionItems" } },
]

const userMenu = [
	{ label: "Desk", icon: "lucide-grid-3x3", onClick: () => (window.location.href = "/app/meeting") },
	{ label: "Apps", icon: "lucide-layers", onClick: () => (window.location.href = "/apps") },
	{ label: "Log out", icon: "lucide-log-out", onClick: () => session.logout() },
]
</script>
