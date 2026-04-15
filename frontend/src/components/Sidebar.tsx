"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
	Crosshair,
	Map,
	Trophy,
	Radio,
	BarChart3,
	BookOpen,
	Zap,
	TrendingUp,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const NAV_ITEMS: { href: string; label: string; icon: LucideIcon }[] = [
	{ href: "/missions", label: "Missions", icon: Crosshair },
	{ href: "/quest-map", label: "Quest Map", icon: Map },
	{ href: "/inventory", label: "Inventory", icon: Trophy },
	{ href: "/comms", label: "Comms Log", icon: Radio },
	{ href: "/profile", label: "Profile", icon: BarChart3 },
];

const ADMIN_ITEMS: { href: string; label: string; icon: LucideIcon }[] = [
	{ href: "/admin/courses", label: "Courses", icon: BookOpen },
	{ href: "/admin/quests", label: "Quests", icon: Zap },
	{ href: "/admin/analytics", label: "Analytics", icon: TrendingUp },
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
							className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200 ${
								active
									? "bg-[#6366F1]/10 text-[#6366F1] font-medium shadow-[inset_0_0_12px_rgba(99,102,241,0.1)]"
									: "text-[#A1A1AA] hover:text-white hover:bg-[#141416] hover:translate-x-1"
							}`}
						>
							<item.icon className="w-4 h-4" />
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
							className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200 ${
								active
									? "bg-[#6366F1]/10 text-[#6366F1] font-medium shadow-[inset_0_0_12px_rgba(99,102,241,0.1)]"
									: "text-[#A1A1AA] hover:text-white hover:bg-[#141416] hover:translate-x-1"
							}`}
						>
							<item.icon className="w-4 h-4" />
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
