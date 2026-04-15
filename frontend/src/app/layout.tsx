import { Toaster } from "sonner";
import type { Metadata } from "next";
import { Geist, Geist_Mono, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
	variable: "--font-geist-sans",
	subsets: ["latin"],
});

const geistMono = Geist_Mono({
	variable: "--font-geist-mono",
	subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
	variable: "--font-jetbrains-mono",
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
			className={`dark ${geistSans.variable} ${geistMono.variable} ${jetbrainsMono.variable} h-full antialiased`}
		>
			<body className="min-h-full flex flex-col bg-background text-foreground">
				{children}
				<Toaster
					theme="dark"
					position="bottom-right"
					toastOptions={{
						style: {
							background: "#141416",
							border: "1px solid #2A2A2E",
							color: "#FAFAFA",
						},
					}}
				/>
			</body>
		</html>
	);
}
