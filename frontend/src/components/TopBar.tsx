"use client";

import { Fragment, type ReactNode } from "react";

export interface Crumb {
	label: string;
	mono?: boolean;
}

interface TopBarProps {
	breadcrumb: Crumb[];
	actions?: ReactNode;
	/** Override the default GM · Online pill with a custom status pill. */
	statusPill?: ReactNode;
}

function DefaultGmPill() {
	return (
		<div
			className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-border-subtle"
			style={{ background: "rgba(16,185,129,0.06)" }}
		>
			<span
				className="w-1.5 h-1.5 rounded-full bg-accent-success"
				style={{ boxShadow: "0 0 8px rgba(16,185,129,0.5)" }}
			/>
			<span className="mono text-[10px] tracking-[0.1em] text-accent-success uppercase">
				GM · Online
			</span>
		</div>
	);
}

/**
 * Top bar with slash-separated breadcrumb + GM status pill + optional actions.
 * Mirrors the NDQS design bundle — last crumb is white/semibold and can be mono.
 */
export default function TopBar({ breadcrumb, actions, statusPill }: TopBarProps) {
	return (
		<div
			className="flex items-center justify-between h-14 px-6 shrink-0 border-b border-border-subtle"
			style={{
				background: "rgba(5,5,10,0.4)",
				backdropFilter: "blur(10px)",
				WebkitBackdropFilter: "blur(10px)",
			}}
		>
			<div className="flex items-center gap-2 text-[13px]">
				{breadcrumb.map((crumb, idx) => {
					const last = idx === breadcrumb.length - 1;
					return (
						<Fragment key={`${crumb.label}-${idx}`}>
							{idx > 0 && <span className="text-text-muted">/</span>}
							<span
								className={
									last
										? crumb.mono
											? "mono text-text-primary font-medium tracking-[-0.01em]"
											: "text-text-primary font-medium"
										: "text-text-secondary"
								}
							>
								{crumb.label}
							</span>
						</Fragment>
					);
				})}
			</div>
			<div className="flex items-center gap-2.5">
				{actions}
				{statusPill ?? <DefaultGmPill />}
			</div>
		</div>
	);
}
