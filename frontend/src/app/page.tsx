"use client";

import Link from "next/link";
import { Gamepad2, Bot, Trophy, Monitor, Shield, BarChart3 } from "lucide-react";
import { FadeInUp, StaggerContainer, StaggerItem } from "@/lib/motion";

export default function LandingPage() {
	return (
		<div className="min-h-screen bg-[#0A0A0B] text-white">
			{/* Hero */}
			<section className="relative overflow-hidden">
				<div className="absolute inset-0 bg-gradient-to-b from-[#6366F1]/10 via-transparent to-transparent" />
				<div className="max-w-5xl mx-auto px-6 pt-20 pb-32 relative">
					<div className="text-center">
						<FadeInUp>
						<p className="text-sm font-mono text-[#6366F1] uppercase tracking-widest mb-4">
							Narrative-Driven Quest Sandbox
						</p>
						</FadeInUp>
						<FadeInUp delay={0.1}>
						<h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
							Learn IT by
							<br />
							<span className="bg-gradient-to-r from-[#6366F1] to-[#22C55E] bg-clip-text text-transparent">
								completing quests
							</span>
						</h1>
						</FadeInUp>
						<FadeInUp delay={0.2}>
						<p className="text-lg text-[#A1A1AA] max-w-2xl mx-auto mb-10 leading-relaxed">
							No more boring lessons. Code in your own IDE, guided by an AI Game Master.
							Every quest is a mission. Every mistake is a plot twist. Every success unlocks new chapters.
						</p>
						</FadeInUp>
						<FadeInUp delay={0.3}>
						<div className="flex gap-4 justify-center">
							<Link
								href="/missions"
								className="px-8 py-4 rounded-xl bg-[#6366F1] text-white font-semibold hover:bg-[#5558E6] active:scale-[0.98] transition-all text-lg"
							>
								Start Your Mission
							</Link>
							<Link
								href="/login"
								className="px-8 py-4 rounded-xl border border-[#2A2A2E] text-[#A1A1AA] font-semibold hover:text-white hover:bg-[#141416] transition-all text-lg"
							>
								Sign In
							</Link>
						</div>
						</FadeInUp>
					</div>
				</div>
			</section>

			{/* Features */}
			<section className="max-w-5xl mx-auto px-6 py-20">
				<h2 className="text-3xl font-bold text-center mb-16">
					Not a course.{" "}
					<span className="text-[#6366F1]">A mission.</span>
				</h2>
				<StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-8">
					{[
						{ icon: Gamepad2, title: "Narrative Quests", desc: "Every lesson is a quest wrapped in a story. You're not studying — you're on a mission." },
						{ icon: Bot, title: "AI Game Master", desc: "An LLM evaluates your work, gives narrative feedback, and guides you with Socratic questions." },
						{ icon: Trophy, title: "Artifacts & Progression", desc: "Complete quests to earn artifacts that unlock new missions. Build your inventory." },
						{ icon: Monitor, title: "Your Own IDE", desc: "Work in VS Code, Claude Code, Cursor — the platform integrates with your tools." },
						{ icon: Shield, title: "Real Security", desc: "Every quest has security checks. Your Game Master calls out vulnerabilities." },
						{ icon: BarChart3, title: "Track Progress", desc: "Visual quest map, quality radar chart, streak counter. See your growth in real time." },
					].map((f) => (
						<StaggerItem key={f.title} className="rounded-2xl border border-[#2A2A2E] backdrop-blur-xl bg-[#141416]/70 p-6 hover:border-[#6366F1]/30 transition-all duration-200 cursor-pointer hover:translate-y-[-2px] hover:shadow-[0_0_20px_rgba(99,102,241,0.1)]">
							<f.icon className="w-8 h-8 text-[#6366F1] mb-4" />
							<h3 className="text-lg font-semibold mb-2">{f.title}</h3>
							<p className="text-sm text-[#A1A1AA] leading-relaxed">{f.desc}</p>
						</StaggerItem>
					))}
				</StaggerContainer>
			</section>

			{/* How it works */}
			<section className="max-w-5xl mx-auto px-6 py-20">
				<h2 className="text-3xl font-bold text-center mb-16">How it works</h2>
				<div className="space-y-8">
					{[
						{ step: "01", title: "Choose your mission", desc: "Browse the catalog and pick an operation." },
						{ step: "02", title: "Download Starter Pack", desc: "Get CLAUDE.md configured for your AI assistant." },
						{ step: "03", title: "Complete quests", desc: "Read briefing. Code. Submit. Get narrative feedback." },
						{ step: "04", title: "Earn artifacts", desc: "Collect artifacts to unlock advanced missions." },
					].map((item) => (
						<div key={item.step} className="flex gap-6 items-start">
							<span className="text-4xl font-bold text-[#6366F1]/30 font-mono shrink-0">{item.step}</span>
							<div>
								<h3 className="text-lg font-semibold mb-1">{item.title}</h3>
								<p className="text-[#A1A1AA]">{item.desc}</p>
							</div>
						</div>
					))}
				</div>
			</section>

			{/* CTA */}
			<section className="max-w-5xl mx-auto px-6 py-20 text-center">
				<div className="rounded-2xl border border-[#2A2A2E] bg-gradient-to-br from-[#141416] to-[#6366F1]/5 p-12">
					<h2 className="text-3xl font-bold mb-4">Ready for your first mission?</h2>
					<p className="text-[#A1A1AA] mb-8">Join the resistance. Start coding. Save the world.</p>
					<Link
						href="/missions"
						className="px-10 py-4 rounded-xl bg-[#6366F1] text-white font-semibold hover:bg-[#5558E6] active:scale-[0.98] transition-all text-lg inline-block"
					>
						Accept Mission
					</Link>
				</div>
			</section>

			<footer className="border-t border-[#2A2A2E] py-8 text-center text-xs text-[#A1A1AA]">
				NDQS Platform — Narrative-Driven Quest Sandbox
			</footer>
		</div>
	);
}
