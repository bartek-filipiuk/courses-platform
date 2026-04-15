"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
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

export default function SidebarProvider({ children }: { children: ReactNode }) {
	const [collapsed, setCollapsed] = useState(false);

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
