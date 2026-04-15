"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
	{ href: "/missions", label: "Missions", icon: "🎯" },
	{ href: "/(dashboard)/quest-map", label: "Quest Map", icon: "🗺️" },
	{ href: "/(dashboard)/inventory", label: "Inventory", icon: "🏆" },
	{ href: "/(dashboard)/comms", label: "Comms Log", icon: "📡" },
	{ href: "/(dashboard)/profile", label: "Profile", icon: "📊" },
];

const ADMIN_ITEMS = [
	{ href: "/admin/courses", label: "Courses", icon: "📝" },
	{ href: "/admin/quests", label: "Quests", icon: "⚡" },
	{ href: "/admin/analytics", label: "Analytics", icon: "📈" },
];

export default function Sidebar() {
	const pathname = usePathname();

	return (
		<aside className="w-64 border-r border-[#2A2A2E] bg-[#0A0A0B] flex flex-col h-screen sticky top-0">
			{/* Logo */}
			<Link href="/" className="px-6 py-5 border-b border-[#2A2A2E]">
				<span className="text-lg font-bold text-white">NDQS</span>
				<span className="text-xs text-[#A1A1AA] ml-2">Platform</span>
			</Link>

			{/* Nav */}
			<nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
				<p className="px-3 text-xs text-[#A1A1AA] uppercase tracking-wider mb-2">Student</p>
				{NAV_ITEMS.map((item) => {
					const active = pathname === item.href || pathname.startsWith(item.href + "/");
					return (
						<Link
							key={item.href}
							href={item.href}
							className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors ${
								active
									? "bg-[#6366F1]/10 text-[#6366F1] font-medium"
									: "text-[#A1A1AA] hover:text-white hover:bg-[#141416]"
							}`}
						>
							<span>{item.icon}</span>
							{item.label}
						</Link>
					);
				})}

				<div className="my-4 border-t border-[#2A2A2E]" />

				<p className="px-3 text-xs text-[#A1A1AA] uppercase tracking-wider mb-2">Admin</p>
				{ADMIN_ITEMS.map((item) => {
					const active = pathname === item.href;
					return (
						<Link
							key={item.href}
							href={item.href}
							className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors ${
								active
									? "bg-[#6366F1]/10 text-[#6366F1] font-medium"
									: "text-[#A1A1AA] hover:text-white hover:bg-[#141416]"
							}`}
						>
							<span>{item.icon}</span>
							{item.label}
						</Link>
					);
				})}
			</nav>

			{/* Footer */}
			<div className="px-6 py-4 border-t border-[#2A2A2E]">
				<p className="text-xs text-[#A1A1AA]">Ghost — student</p>
			</div>
		</aside>
	);
}
