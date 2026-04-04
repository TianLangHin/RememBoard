export type MoveStruct = {
  moveNum: number,
  white: string,
  black: string,
}

export function getMoveList(moves: string[]): MoveStruct[] {
  const halfPlies = moves.length >> 1

  const movesFromBothPlayers = Array.from(Array(halfPlies).keys())
    .map(i => ({
      moveNum: i + 1,
      white: moves[2 * i],
      black: moves[2 * i + 1],
    }))

  const lastMove = moves.length % 2 === 1
    ? [{moveNum: halfPlies + 1, white: moves[moves.length - 1], black: ''}]
    : []

  return [...movesFromBothPlayers, ...lastMove]
}
