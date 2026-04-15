import SidebarProvider from "@/components/SidebarProvider";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
	return <SidebarProvider>{children}</SidebarProvider>;
}
