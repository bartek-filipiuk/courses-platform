"use client";

import { useState, useEffect } from "react";

export function useTypewriter(text: string, speed = 30) {
	const [displayed, setDisplayed] = useState("");
	const [isTyping, setIsTyping] = useState(false);

	useEffect(() => {
		const prefersReduced = window.matchMedia(
			"(prefers-reduced-motion: reduce)",
		).matches;

		if (prefersReduced) {
			setDisplayed(text);
			setIsTyping(false);
			return;
		}

		setIsTyping(true);
		setDisplayed("");
		let i = 0;

		const interval = setInterval(() => {
			setDisplayed(text.slice(0, i + 1));
			i++;
			if (i >= text.length) {
				clearInterval(interval);
				setIsTyping(false);
			}
		}, speed + Math.random() * 40);

		return () => clearInterval(interval);
	}, [text, speed]);

	return { displayText: displayed, isTyping };
}
