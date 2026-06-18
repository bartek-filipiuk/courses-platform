import AuthGate from "@/components/AuthGate";
import SidebarProvider from "@/components/SidebarProvider";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
	return (
		<AuthGate>
			<SidebarProvider>{children}</SidebarProvider>
		</AuthGate>
	);
}
