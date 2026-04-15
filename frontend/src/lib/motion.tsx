"use client";

import { motion, AnimatePresence, type Variants } from "framer-motion";
import type { ReactNode } from "react";

// --- Variants (spring physics) ---

export const fadeInUp: Variants = {
	hidden: { opacity: 0, y: 20 },
	visible: {
		opacity: 1,
		y: 0,
		transition: { type: "spring", stiffness: 300, damping: 24 },
	},
};

export const fadeIn: Variants = {
	hidden: { opacity: 0 },
	visible: { opacity: 1, transition: { duration: 0.3 } },
};

export const slideInRight: Variants = {
	hidden: { opacity: 0, x: 40 },
	visible: {
		opacity: 1,
		x: 0,
		transition: { type: "spring", stiffness: 300, damping: 24 },
	},
	exit: { opacity: 0, x: 40, transition: { duration: 0.2 } },
};

export const scaleIn: Variants = {
	hidden: { opacity: 0, scale: 0.95 },
	visible: {
		opacity: 1,
		scale: 1,
		transition: { type: "spring", stiffness: 400, damping: 25 },
	},
};

export const staggerContainer: Variants = {
	hidden: { opacity: 0 },
	visible: {
		opacity: 1,
		transition: { staggerChildren: 0.08, delayChildren: 0.1 },
	},
};

export const staggerItem: Variants = {
	hidden: { opacity: 0, y: 16 },
	visible: {
		opacity: 1,
		y: 0,
		transition: { type: "spring", stiffness: 300, damping: 24 },
	},
};

export const pageTransition: Variants = {
	initial: { opacity: 0, y: 8 },
	animate: { opacity: 1, y: 0 },
	exit: { opacity: 0, y: -8 },
};

// --- Components ---

export function FadeInUp({
	children,
	className,
	delay = 0,
}: { children: ReactNode; className?: string; delay?: number }) {
	return (
		<motion.div
			initial="hidden"
			animate="visible"
			variants={fadeInUp}
			transition={{ delay }}
			className={className}
		>
			{children}
		</motion.div>
	);
}

export function StaggerContainer({
	children,
	className,
}: { children: ReactNode; className?: string }) {
	return (
		<motion.div
			initial="hidden"
			animate="visible"
			variants={staggerContainer}
			className={className}
		>
			{children}
		</motion.div>
	);
}

export function StaggerItem({
	children,
	className,
}: { children: ReactNode; className?: string }) {
	return (
		<motion.div variants={staggerItem} className={className}>
			{children}
		</motion.div>
	);
}

export function SlideInPanel({
	children,
	className,
	show,
}: { children: ReactNode; className?: string; show: boolean }) {
	return (
		<AnimatePresence>
			{show && (
				<motion.div
					initial="hidden"
					animate="visible"
					exit="exit"
					variants={slideInRight}
					className={className}
				>
					{children}
				</motion.div>
			)}
		</AnimatePresence>
	);
}

export function ScaleIn({
	children,
	className,
}: { children: ReactNode; className?: string }) {
	return (
		<motion.div
			initial="hidden"
			animate="visible"
			variants={scaleIn}
			className={className}
		>
			{children}
		</motion.div>
	);
}

export function PageTransition({
	children,
	className,
}: { children: ReactNode; className?: string }) {
	return (
		<motion.div
			initial={{ opacity: 0, y: 8 }}
			animate={{ opacity: 1, y: 0 }}
			exit={{ opacity: 0, y: -8 }}
			transition={{ duration: 0.2, ease: "easeInOut" }}
			className={className}
		>
			{children}
		</motion.div>
	);
}

// Re-export motion for inline use
export { motion, AnimatePresence };
