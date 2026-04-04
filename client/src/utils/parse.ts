export type ServerPayload = {
  status: string,
  diagnostics: string,
  player1: string,
  player2: string,
  paused: boolean,
  concluded: string,
  fen: string,
  moves: string[],
  orientation: string,
  imageContent: string,
}

export function parseServerPayload(payload: string): ServerPayload | null {
  var payloadRegex = new RegExp(
    "status<(valid|invalid|ambiguous|obstructed)<([A-Za-z0-9 .,]*)>>" +
    "game<" +
    "p1<([A-Za-z0-9]*)>" +
    "p2<([A-Za-z0-9]*)>" +
    "paused<(0|1)>" +
    "concluded<(1-0|1[/]2-1[/]2|0-1|[*])>" +
    "fen<([A-Za-z0-9/ -]+)>" +
    "moves<([A-Za-z0-9+#-|]*)>" +
    "orientation<(a1|a8|h1|h8)>" +
    ">" +
    "img<([A-Za-z0-9+/=]*)>"
  )

  const match = payload.match(payloadRegex)
  if (match === null) {
    return null
  }

  return {
    status: match[1],
    diagnostics: match[2],
    player1: match[3],
    player2: match[4],
    paused: match[5] === '1',
    concluded: match[6],
    fen: match[7],
    moves: match[8].split('|'),
    orientation: match[9],
    imageContent: match[10],
  }
}
