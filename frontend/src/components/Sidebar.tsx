"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
	BookOpen,
	ChevronDown,
	Key,
	MessageSquare,
	Map as MapIcon,
	Package,
	Settings,
	ShoppingBag,
	TrendingUp,
	Zap,
	ChevronLeft,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSidebar } from "./SidebarProvider";
import { useAuthFetch } from "@/lib/use-api";

interface EnrollmentSummary {
	course_id: string;
	title: string;
	narrative_title: string | null;
	persona_name: string | null;
	cover_image_url: string | null;
	total_quests: number;
	completed_quests: number;
	progress_pct: number;
}

interface NavItem {
	href: string;
	label: string;
	icon: LucideIcon;
	badge?: string;
}

function Logo({ collapsed }: { collapsed: boolean }) {
	return (
		<div className="flex items-center gap-2.5 px-4 pt-4 pb-5">
			<div
				className="w-7 h-7 rounded-md flex items-center justify-center font-mono font-bold text-[13px] text-bg-base shrink-0"
				style={{
					background: "linear-gradient(135deg, #E5B55C, #7C3AED)",
					boxShadow: "0 0 18px rgba(229,181,92,0.35)",
				}}
			>
				◆
			</div>
			{!collapsed && (
				<div>
					<div className="mono text-[13px] font-semibold tracking-[0.08em]">
						NDQS<span className="text-accent-primary">_</span>
					</div>
					<div className="mini-label mt-0.5">Command Center</div>
				</div>
			)}
		</div>
	);
}

function ActiveOperationCard({
	enrollment,
}: {
	enrollment: EnrollmentSummary;
}) {
	const displayTitle = (enrollment.narrative_title || enrollment.title)
		.replace(/^Operation: /i, "")
		.replace(/^Operacja: /i, "");
	return (
		<Link
			href={`/quest-map?courseId=${enrollment.course_id}`}
			className="glass flex items-center gap-2.5 w-full px-3 py-2.5 text-left cursor-pointer"
			style={{
				border: "1px solid rgba(229,181,92,0.2)",
				background: "rgba(229,181,92,0.05)",
			}}
		>
			<div
				className="w-7 h-7 rounded-md shrink-0"
				style={{
					background: "linear-gradient(135deg, #7C3AED, #E5B55C)",
				}}
			/>
			<div className="flex-1 min-w-0">
				<div className="text-[13px] font-semibold text-text-primary truncate">
					{displayTitle}
				</div>
				<div className="mono text-[10px] text-text-secondary mt-0.5">
					{enrollment.persona_name?.toUpperCase() || "GM"} · ACTIVE
				</div>
			</div>
			<ChevronDown className="w-3.5 h-3.5 text-text-secondary" />
		</Link>
	);
}

function NavItemButton({
	item,
	active,
	collapsed,
}: {
	item: NavItem;
	active: boolean;
	collapsed: boolean;
}) {
	return (
		<Link
			href={item.href}
			title={collapsed ? item.label : undefined}
			className={cn(
				"relative flex items-center gap-3 text-sm font-medium transition-all duration-200 mx-2.5 my-0.5 rounded-[10px] border",
				collapsed ? "justify-center p-2.5" : "px-3 py-2.5",
				active
					? "text-accent-primary border-accent-primary/20"
					: "text-text-secondary border-transparent hover:text-text-primary hover:bg-bg-surface-hover",
			)}
			style={
				active
					? { background: "rgba(229,181,92,0.08)" }
					: undefined
			}
		>
			{active && (
				<span
					className="absolute -left-2.5 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-[3px] bg-accent-primary"
					style={{ boxShadow: "0 0 8px rgba(229,181,92,0.6)" }}
				/>
			)}
			<item.icon className="w-[18px] h-[18px] shrink-0" />
			{!collapsed && (
				<>
					<span className="flex-1">{item.label}</span>
					{item.badge && (
						<span className="mono text-[10px] px-1.5 py-0.5 rounded bg-accent-primary/15 text-accent-primary tracking-wider">
							{item.badge}
						</span>
					)}
				</>
			)}
		</Link>
	);
}

export default function Sidebar() {
	const pathname = usePathname();
	const { collapsed, toggle } = useSidebar();
	const { data: enrollments } = useAuthFetch<EnrollmentSummary[]>(
		"/api/users/me/enrollments",
	);
	const activeEnrollment = enrollments?.[0] ?? null;

	const questMapHref = activeEnrollment
		? `/quest-map?courseId=${activeEnrollment.course_id}`
		: "/quest-map";
	const commsHref = activeEnrollment
		? `/comms?courseId=${activeEnrollment.course_id}`
		: "/comms";

	const questProgressBadge = activeEnrollment
		? `${activeEnrollment.completed_quests}/${activeEnrollment.total_quests}`
		: undefined;

	const studentNav: NavItem[] = [
		{ href: "/missions", label: "Marketplace", icon: ShoppingBag },
		{ href: questMapHref, label: "Quest Map", icon: MapIcon, badge: questProgressBadge },
		{ href: commsHref, label: "Comms Log", icon: MessageSquare },
		{ href: "/inventory", label: "Inventory", icon: Package },
		{ href: "/profile", label: "API Key", icon: Key },
	];

	const adminNav: NavItem[] = [
		{ href: "/admin/courses", label: "Courses", icon: BookOpen },
		{ href: "/admin/quests", label: "Quests", icon: Zap },
		{ href: "/admin/analytics", label: "Analytics", icon: TrendingUp },
	];

	const isActive = (href: string) => {
		const base = href.split("?")[0];
		return pathname === base || pathname.startsWith(`${base}/`);
	};

	return (
		<aside
			className="flex flex-col h-screen sticky top-0 border-r border-border-subtle transition-[width] duration-300 relative z-[5] shrink-0"
			style={{
				width: collapsed ? 68 : 240,
				background: "rgba(8,8,15,0.75)",
				backdropFilter: "blur(16px)",
				WebkitBackdropFilter: "blur(16px)",
			}}
		>
			<Logo collapsed={collapsed} />

			{!collapsed && activeEnrollment && (
				<div className="px-3.5 pb-4">
					<div className="mini-label mb-2">Active Operation</div>
					<ActiveOperationCard enrollment={activeEnrollment} />
				</div>
			)}

			<nav className="flex-1 pt-1">
				{!collapsed && (
					<div className="mini-label px-6 pb-1.5">Navigation</div>
				)}
				{studentNav.map((item) => (
					<NavItemButton
						key={item.href}
						item={item}
						active={isActive(item.href)}
						collapsed={collapsed}
					/>
				))}
				<div className="mx-3 my-3 border-t border-border-subtle" />
				{!collapsed && <div className="mini-label px-6 pb-1.5">Admin</div>}
				{adminNav.map((item) => (
					<NavItemButton
						key={item.href}
						item={item}
						active={isActive(item.href)}
						collapsed={collapsed}
					/>
				))}
			</nav>

			{!collapsed && activeEnrollment && (
				<div className="px-3.5 py-3.5 border-t border-border-subtle">
					<div className="mini-label mb-2">Operation Progress</div>
					<div className="segbar">
						{Array.from({ length: activeEnrollment.total_quests }).map(
							(_, idx) => {
								const done = idx < activeEnrollment.completed_quests;
								const active = idx === activeEnrollment.completed_quests;
								return (
									<div
										key={idx}
										className={cn(
											"seg",
											done && "done",
											active && "active",
										)}
									/>
								);
							},
						)}
					</div>
					<div className="flex justify-between mt-2.5 text-[11px] text-text-secondary">
						<span className="mono">
							{activeEnrollment.completed_quests} / {activeEnrollment.total_quests} QUESTS
						</span>
						<span className="mono text-accent-primary">
							{Math.round(activeEnrollment.progress_pct)}%
						</span>
					</div>
				</div>
			)}

			<div className="flex items-center gap-2.5 px-3.5 py-3.5 border-t border-border-subtle">
				<div
					className="w-8 h-8 rounded-lg flex items-center justify-center text-[12px] font-bold text-bg-base shrink-0"
					style={{ background: "linear-gradient(135deg, #7C3AED, #E5B55C)" }}
				>
					G
				</div>
				{!collapsed && (
					<>
						<div className="flex-1 min-w-0">
							<div className="text-[13px] font-medium">Ghost</div>
							<div className="mono text-[10px] text-text-secondary">agent_ghost</div>
						</div>
						<button
							type="button"
							className="text-text-muted hover:text-text-secondary transition-colors"
							aria-label="Settings"
						>
							<Settings className="w-4 h-4" />
						</button>
					</>
				)}
			</div>

			<button
				type="button"
				onClick={toggle}
				aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
				className="absolute top-[22px] -right-3 w-6 h-6 rounded-full flex items-center justify-center text-text-secondary transition-transform duration-300 z-10"
				style={{
					background: "#0B0B15",
					border: "1px solid rgba(255,255,255,0.1)",
					transform: collapsed ? "rotate(180deg)" : "none",
				}}
			>
				<ChevronLeft className="w-3.5 h-3.5" />
			</button>
		</aside>
	);
}
