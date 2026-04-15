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
	PanelLeftClose,
	PanelLeftOpen,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSidebar } from "./SidebarProvider";

const NAV_ITEMS: { href: string; label: string; icon: LucideIcon }[] = [
	{ href: "/missions", label: "Missions", icon: Crosshair },
	{ href: "/my-courses", label: "My Courses", icon: BookOpen },
	{ href: "/inventory", label: "Inventory", icon: Trophy },
	{ href: "/profile", label: "Profile", icon: BarChart3 },
];

const ADMIN_ITEMS: { href: string; label: string; icon: LucideIcon }[] = [
	{ href: "/admin/courses", label: "Courses", icon: BookOpen },
	{ href: "/admin/quests", label: "Quests", icon: Zap },
	{ href: "/admin/analytics", label: "Analytics", icon: TrendingUp },
];

export default function Sidebar() {
	const pathname = usePathname();
	const { collapsed, toggle } = useSidebar();

	return (
		<aside
			className={cn(
				"border-r border-border-subtle bg-bg-sidebar flex flex-col h-screen sticky top-0 transition-all duration-300",
				collapsed ? "w-[56px]" : "w-60",
			)}
		>
			{/* Logo */}
			<div className="flex items-center justify-between px-4 py-4 border-b border-border-subtle">
				<Link href="/" className="flex items-center gap-2 overflow-hidden">
					<span className="text-lg font-bold text-accent-primary font-mono shrink-0">N</span>
					{!collapsed && (
						<>
							<span className="text-lg font-bold text-text-primary">DQS</span>
							<span className="text-xs text-text-muted ml-1">Platform</span>
						</>
					)}
				</Link>
				<button
					type="button"
					onClick={toggle}
					className="text-text-muted hover:text-text-primary transition-colors shrink-0"
					aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
				>
					{collapsed ? (
						<PanelLeftOpen className="w-4 h-4" />
					) : (
						<PanelLeftClose className="w-4 h-4" />
					)}
				</button>
			</div>

			{/* Nav */}
			<nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
				{!collapsed && (
					<p className="px-3 text-xs text-text-muted uppercase tracking-wider mb-2">
						Student
					</p>
				)}
				{collapsed && <div className="mb-2 border-b border-border-subtle" />}
				{NAV_ITEMS.map((item) => {
					const active =
						pathname === item.href ||
						pathname.startsWith(`${item.href}/`);
					return (
						<Link
							key={item.href}
							href={item.href}
							title={collapsed ? item.label : undefined}
							className={cn(
								"flex items-center gap-3 py-2.5 rounded-xl text-sm transition-all duration-200",
								collapsed ? "justify-center px-2" : "px-3",
								active
									? "bg-accent-primary/10 text-accent-primary font-medium shadow-[inset_0_0_12px_var(--accent-glow)]"
									: "text-text-secondary hover:text-text-primary hover:bg-bg-surface-hover",
							)}
						>
							<item.icon className="w-4 h-4 shrink-0" />
							{!collapsed && item.label}
						</Link>
					);
				})}

				<div className="my-4 border-t border-border-subtle" />

				{!collapsed && (
					<p className="px-3 text-xs text-text-muted uppercase tracking-wider mb-2">
						Admin
					</p>
				)}
				{ADMIN_ITEMS.map((item) => {
					const active = pathname === item.href;
					return (
						<Link
							key={item.href}
							href={item.href}
							title={collapsed ? item.label : undefined}
							className={cn(
								"flex items-center gap-3 py-2.5 rounded-xl text-sm transition-all duration-200",
								collapsed ? "justify-center px-2" : "px-3",
								active
									? "bg-accent-primary/10 text-accent-primary font-medium shadow-[inset_0_0_12px_var(--accent-glow)]"
									: "text-text-secondary hover:text-text-primary hover:bg-bg-surface-hover",
							)}
						>
							<item.icon className="w-4 h-4 shrink-0" />
							{!collapsed && item.label}
						</Link>
					);
				})}
			</nav>

			{/* Footer */}
			<div className="px-4 py-4 border-t border-border-subtle">
				{collapsed ? (
					<div className="w-6 h-6 rounded-full bg-accent-primary/20 mx-auto" />
				) : (
					<p className="text-xs text-text-muted">Ghost — student</p>
				)}
			</div>
		</aside>
	);
}
