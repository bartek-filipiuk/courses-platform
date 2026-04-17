/**
 * Quest Map layout: snake pattern — left-to-right on even rows, right-to-left
 * on odd rows, so the chain reads like a game board.
 *
 * 3 columns × N rows. Node centers are at the returned (x,y) so that edges
 * drawn from centers + half-width produce clean side connections.
 */

export interface NodePosition {
	x: number;
	y: number;
}

const COL_X = [300, 640, 980];
const ROW_Y_START = 140;
const ROW_HEIGHT = 160;

export function questPosition(sortOrderZeroBased: number): NodePosition {
	const row = Math.floor(sortOrderZeroBased / 3);
	const col = sortOrderZeroBased % 3;
	const actualCol = row % 2 === 0 ? col : 2 - col;
	return {
		x: COL_X[actualCol],
		y: ROW_Y_START + row * ROW_HEIGHT,
	};
}

export function mapDimensions(totalQuests: number): { width: number; height: number } {
	const rows = Math.ceil(totalQuests / 3);
	return {
		width: 1280,
		height: ROW_Y_START + rows * ROW_HEIGHT + 40,
	};
}

export const NODE_WIDTH = 180;
export const NODE_HEIGHT = 90;

/**
 * Compute a bezier path between two node centers with smart anchor side
 * selection. When nodes are in the same row → horizontal side-to-side edge.
 * Otherwise → vertical S-curve using mid-y control points.
 */
export function edgePath(from: NodePosition, to: NodePosition): string {
	const sameRow = Math.abs(to.y - from.y) < 20;
	if (sameRow) {
		const goingRight = to.x > from.x;
		const x1 = from.x + (goingRight ? NODE_WIDTH / 2 : -NODE_WIDTH / 2);
		const x2 = to.x + (goingRight ? -NODE_WIDTH / 2 : NODE_WIDTH / 2);
		const y1 = from.y;
		const y2 = to.y;
		const mx = (x1 + x2) / 2;
		return `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
	}
	// Row switch: exit the bottom of the upper node, enter the top of the lower one.
	const goingDown = to.y > from.y;
	const y1 = from.y + (goingDown ? NODE_HEIGHT / 2 : -NODE_HEIGHT / 2);
	const y2 = to.y + (goingDown ? -NODE_HEIGHT / 2 : NODE_HEIGHT / 2);
	const x1 = from.x;
	const x2 = to.x;
	const midY = (y1 + y2) / 2;
	return `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
}
