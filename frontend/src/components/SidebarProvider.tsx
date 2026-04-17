"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import Sidebar from "./Sidebar";

interface SidebarContextValue {
	collapsed: boolean;
	toggle: () => void;
}

const SidebarContext = createContext<SidebarContextValue>({
	collapsed: false,
	toggle: () => {},
});

export function useSidebar() {
	return useContext(SidebarContext);
}

const STORAGE_KEY = "ndqs.sidebar.collapsed";

export default function SidebarProvider({ children }: { children: ReactNode }) {
	const [collapsed, setCollapsed] = useState(false);

	// Hydrate from localStorage on mount (client-only).
	useEffect(() => {
		try {
			const saved = localStorage.getItem(STORAGE_KEY);
			if (saved !== null) setCollapsed(saved === "1");
		} catch {
			/* localStorage unavailable — keep default */
		}
	}, []);

	useEffect(() => {
		try {
			localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
		} catch {
			/* ignore */
		}
	}, [collapsed]);

	return (
		<SidebarContext.Provider
			value={{ collapsed, toggle: () => setCollapsed((c) => !c) }}
		>
			<div className="flex min-h-screen">
				<Sidebar />
				<main className="flex-1 overflow-auto">{children}</main>
			</div>
		</SidebarContext.Provider>
	);
}
