<template>
	<!-- frappe-ui's settings dialog, laid out like Frappe Drive's. Meeting keeps Account,
	     plus Users for managers; workspace and storage settings belong to Suite and Drive. -->
	<SettingsDialog v-model:open="open" v-model:tab="tab" size="5xl" :keyboard-shortcut="false">
		<template #title>Settings</template>
		<SettingsSidebar>
			<SettingsNavGroup label="Account">
				<SettingsNavItem value="profile">
					<template #prefix>
						<Avatar
							:image="session.userImage"
							:label="session.fullName"
							size="xs"
							class="shrink-0"
						/>
					</template>
					Profile
				</SettingsNavItem>
				<SettingsNavItem value="preferences">
					<template #prefix>
						<Icon
							name="lucide-sliders-horizontal"
							class="size-4 shrink-0 text-ink-gray-6"
						/>
					</template>
					Preferences
				</SettingsNavItem>
			</SettingsNavGroup>
			<SettingsNavGroup v-if="session.isManager" label="Administration">
				<SettingsNavItem value="users">
					<template #prefix>
						<Icon name="lucide-users" class="size-4 shrink-0 text-ink-gray-6" />
					</template>
					Users
				</SettingsNavItem>
			</SettingsNavGroup>
		</SettingsSidebar>
		<SettingsContent>
			<SettingsPanel value="profile"><ProfileSettings /></SettingsPanel>
			<SettingsPanel value="preferences"><PreferencesSettings /></SettingsPanel>
			<SettingsPanel v-if="session.isManager" value="users"><UsersSettings /></SettingsPanel>
		</SettingsContent>
	</SettingsDialog>
</template>

<script setup>
import {
	Avatar,
	Icon,
	SettingsContent,
	SettingsDialog,
	SettingsNavGroup,
	SettingsNavItem,
	SettingsPanel,
	SettingsSidebar,
} from "frappe-ui";
import PreferencesSettings from "@/components/settings/PreferencesSettings.vue";
import ProfileSettings from "@/components/settings/ProfileSettings.vue";
import UsersSettings from "@/components/settings/UsersSettings.vue";
import { session } from "@/data/session";

const open = defineModel("open", { type: Boolean, default: false });
const tab = defineModel("tab", { type: String, default: "profile" });
</script>
