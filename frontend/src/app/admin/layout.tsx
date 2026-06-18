import AuthGate from "@/components/AuthGate";
import SidebarProvider from "@/components/SidebarProvider";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
	return (
		<AuthGate requireAdmin>
			<SidebarProvider>{children}</SidebarProvider>
		</AuthGate>
	);
}
