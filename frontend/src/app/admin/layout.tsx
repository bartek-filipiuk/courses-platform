import SidebarProvider from "@/components/SidebarProvider";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
	return <SidebarProvider>{children}</SidebarProvider>;
}
