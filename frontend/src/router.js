import { createRouter, createWebHistory } from "vue-router";

const routes = [
	{
		path: "/meeting",
		component: () => import("@/components/AppLayout.vue"),
		children: [
			{ path: "", name: "Home", component: () => import("@/pages/Home.vue") },
			{
				path: "meetings",
				name: "Meetings",
				component: () => import("@/pages/Meetings.vue"),
			},
			{
				path: "meetings/new",
				name: "NewMeeting",
				component: () => import("@/pages/MeetingForm.vue"),
			},
			{
				path: "meetings/:name",
				name: "Meeting",
				component: () => import("@/pages/MeetingDetail.vue"),
				props: true,
			},
			{
				path: "meetings/:name/edit",
				name: "EditMeeting",
				component: () => import("@/pages/MeetingForm.vue"),
				props: true,
			},
			{
				path: "action-items",
				name: "ActionItems",
				component: () => import("@/pages/ActionItems.vue"),
			},
		],
	},
	{ path: "/:pathMatch(.*)*", redirect: "/meeting" },
];

export default createRouter({
	history: createWebHistory(),
	routes,
});
