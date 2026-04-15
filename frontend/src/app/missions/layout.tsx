import SidebarProvider from "@/components/SidebarProvider";

export default function MissionsLayout({ children }: { children: React.ReactNode }) {
	return <SidebarProvider>{children}</SidebarProvider>;
}
