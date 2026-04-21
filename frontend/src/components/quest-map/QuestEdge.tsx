"use client";

import { edgePath, type NodePosition } from "./layout";

interface Props {
	from: NodePosition;
	to: NodePosition;
	active: boolean;
	pathId: string;
}

/**
 * SVG edge between two quest nodes. When `active` is true we render a solid
 * gold path + a motion dot that travels along it; otherwise it's a dashed
 * subtle rail.
 */
export default function QuestEdge({ from, to, active, pathId }: Props) {
	const d = edgePath(from, to);
	const color = active ? "#E5B55C" : "rgba(255,255,255,0.1)";

	return (
		<g>
			<path
				d={d}
				id={pathId}
				stroke={color}
				strokeWidth={active ? 1.5 : 1}
				fill="none"
				strokeDasharray={active ? undefined : "4 4"}
				style={{
					filter: active
						? "drop-shadow(0 0 6px rgba(229,181,92,0.4))"
						: undefined,
				}}
			/>
			{active && (
				<circle r={2.5} fill="#E5B55C" style={{ filter: "drop-shadow(0 0 4px #E5B55C)" }}>
					<animateMotion dur="3s" repeatCount="indefinite">
						<mpath href={`#${pathId}`} />
					</animateMotion>
				</circle>
			)}
		</g>
	);
}
