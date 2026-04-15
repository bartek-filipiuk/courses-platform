import { Toaster } from "sonner";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuroraBackground } from "@/components/AuroraBackground";
import "./globals.css";

const geistSans = Geist({
	variable: "--font-geist-sans",
	subsets: ["latin"],
});

const geistMono = Geist_Mono({
	variable: "--font-geist-mono",
	subsets: ["latin"],
});

export const metadata: Metadata = {
	title: "NDQS — Narrative-Driven Quest Sandbox",
	description:
		"IT courses wrapped in narrative quests. Learn by doing, guided by an AI Game Master.",
};

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html
			lang="en"
			className={`dark ${geistSans.variable} ${geistMono.variable} h-full antialiased`}
		>
			<body className="min-h-full flex flex-col bg-bg-base text-text-primary">
				<AuroraBackground />
				{children}
				<Toaster
					theme="dark"
					position="bottom-right"
					toastOptions={{
						style: {
							background: "var(--bg-elevated)",
							border: "1px solid var(--border-default)",
							color: "var(--text-primary)",
						},
					}}
				/>
			</body>
		</html>
	);
}
