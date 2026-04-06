import { useState, useRef, useEffect } from 'react'
import './App.css'

import { type ServerPayload, parseServerPayload } from './utils/parse.ts'
import { Button, FormControl, Grid, InputLabel, List, ListItem, MenuItem, Paper, Select, TextField, Typography } from '@mui/material'
import { ThemeProvider, createTheme } from '@mui/material/styles'

function App() {
  const theme = createTheme({
    colorSchemes: {
      dark: true,
      light: true,
    },
  })

  const [pings, setPings] = useState(0)
  const [pinging, setPinging] = useState(false)

  const [gameInfo, setGameInfo] = useState<ServerPayload[]>([])

  // TextField for a live camera endpoint to add a new game.
  const [stream, setStream] = useState('')
  // Chooses the game to focus custom commands on, so that they all use the same text fields.
  const [selectedGame, setSelectedGame] = useState<number>(0)

  // TextFields for pushing a move and player names of a game, and the camera orientation.
  const [uciMove, setUciMove] = useState('')
  const [playerOne, setPlayerOne] = useState('PlayerOne')
  const [playerTwo, setPlayerTwo] = useState('PlayerTwo')
  const [orientation, setOrientation] = useState('h8')

  const connection = useRef<WebSocket | null>(null)
  useEffect(() => {
    const socket = new WebSocket('ws://localhost:19941')
    socket.addEventListener('open', _ => {
      socket.send('controller')
    })
    connection.current = socket
    return () => connection.current?.close()
  }, [])

  // Receives data.
  useEffect(() => {
    const responder = (event: MessageEvent<any>) => {
      setPings(p => p + 1)

      const gamePayloads = event.data.split('%')
      const parsedPayloads = gamePayloads
        .map((payload: string) => parseServerPayload(payload))
        .filter((payload: ServerPayload | null) => payload !== null)
      setGameInfo(parsedPayloads)

      if (pinging) {
        connection.current?.send('inference')
      }
    }
    connection.current?.addEventListener('message', responder)
    return () => connection.current?.removeEventListener('message', responder)
  }, [pinging])

  // Triggers inference upon change of pinging.
  useEffect(() => {
    if (pinging) {
      connection.current?.send('inference')
    }
  }, [pinging])

  const addGame = () => {
    connection.current?.send(`addgame ${playerOne} ${playerTwo} ${orientation} ${stream}`)
  }

  const removeGame = () => {
    connection.current?.send(`removegame ${selectedGame}`)
  }

  const pushMove = () => {
    connection.current?.send(`makemove ${selectedGame} ${uciMove}`)
  }

  const undoMove = () => {
    connection.current?.send(`undomove ${selectedGame}`)
  }

  const pauseGame = () => {
    connection.current?.send(`pausegame ${selectedGame}`)
  }

  const unpauseGame = () => {
    connection.current?.send(`unpausegame ${selectedGame}`)
  }

  const renamePlayers = () => {
    connection.current?.send(`renameplayers ${selectedGame} ${playerOne} ${playerTwo}`)
  }

  const reorientGame = () => {
    connection.current?.send(`reorient ${selectedGame} ${orientation}`)
  }

  return (
    <ThemeProvider theme={theme}>
      <Grid container spacing={2} sx={{width: '100%'}}>
        {/* Row 1. */}
        <Grid size={12}>
          <Paper sx={{height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <h1>RememBoard Controller</h1>
          </Paper>
        </Grid>
        {/* Row 2. */}
        <Grid size={12}>
          <Paper elevation={2}>
            <Grid container sx={{width: '100%', p: 2}}>
              <Grid size={6}>
                <p>Server Pings: {pings}</p>
              </Grid>
              <Grid size={6}>
                <Button variant="contained" onClick={() => setPinging(p => !p)} sx={{height: '100%'}}>
                  Toggle Server Pinging
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        {/* Row 3. */}
        <Grid size={12}>
          <Paper elevation={2}>
            <Grid container sx={{width: '100%', p: 2}}>
              <Grid size={6}>
                <TextField
                  variant="outlined"
                  label="Stream URI"
                  value={stream}
                  onChange={e => setStream(e.target.value)} sx={{width: '70%'}} />
              </Grid>
              <Grid size={6}>
                <Button variant="contained" onClick={addGame} sx={{height: '100%'}}>Add Game</Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        {/* Row 4. */}
        <Grid size={12}>
          <Paper elevation={3}>
            <Grid container spacing={2} sx={{width: '100%', p: 2}}>
              {/* Row 4a. */}
              <Grid size={6}>
                <TextField
                  variant="outlined"
                  label="Game Number"
                  type="number"
                  value={selectedGame}
                  onChange={e => setSelectedGame(Number(e.target.value))} />
              </Grid>
              <Grid size={6}>
                <Button variant="contained" onClick={removeGame} sx={{height: '100%'}}>Remove Game</Button>
              </Grid>
              {/* Row 4b. */}
              <Grid size={6}>
                <TextField
                  variant="outlined"
                  label="UCI Move"
                  value={uciMove}
                  onChange={e => setUciMove(e.target.value)} />
              </Grid>
              <Grid size={1}>
              </Grid>
              <Grid size={2}>
                <Button variant="contained" onClick={pushMove} sx={{height: '100%'}}>Make Move</Button>
              </Grid>
              <Grid size={2}>
                <Button variant="contained" onClick={undoMove} sx={{height: '100%'}}>Undo Move</Button>
              </Grid>
              <Grid size={1}>
              </Grid>
              {/* Row 4c. */}
              <Grid size={3}>
                <TextField
                  variant="outlined"
                  label="White Player Name"
                  value={playerOne}
                  onChange={e => setPlayerOne(e.target.value)} />
              </Grid>
              <Grid size={3}>
                <TextField
                  variant="outlined"
                  label="Black Player Name"
                  value={playerTwo}
                  onChange={e => setPlayerTwo(e.target.value)} />
              </Grid>
              <Grid size={6}>
                <Button variant="contained" onClick={renamePlayers} sx={{height: '100%'}}>Rename Players</Button>
              </Grid>
              {/* Row 4d. */}
              <Grid size={6}>
                <FormControl sx={{width: '30%'}}>
                  <InputLabel>Top-Left Corner</InputLabel>
                  <Select
                    value={orientation}
                    defaultValue={'h8'}
                    label="Top-Left Corner"
                    onChange={e => setOrientation(e.target.value)}>
                    <MenuItem value={'a1'}>A1</MenuItem>
                    <MenuItem value={'a8'}>A8</MenuItem>
                    <MenuItem value={'h1'}>H1</MenuItem>
                    <MenuItem value={'h8'}>H8</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={6}>
                <Button variant="contained" onClick={reorientGame} sx={{height: '100%'}}>Reorient Game</Button>
              </Grid>
              {/* Row 4e. */}
              <Grid size={3}>
              </Grid>
              <Grid size={3}>
                <Button variant="contained" onClick={pauseGame}>Pause Game</Button>
              </Grid>
              <Grid size={3}>
                <Button variant="contained" onClick={unpauseGame}>Unpause Game</Button>
              </Grid>
              <Grid size={3}>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
      <List>
      {
        Array.from(gameInfo.entries()).map(
          ([index, game]) => (
            <ListItem key={index}>
              <Paper>
                <h3>Game Index {index}</h3>
                <p>Status: {game.status}</p>
                <p>Diagnostics: {game.diagnostics}</p>
                <p>Player 1: {game.player1}</p>
                <p>Player 2: {game.player2}</p>
                <p>Paused: {game.paused ? 'True' : 'False'}</p>
                <p>Conclusion: {game.concluded}</p>
                <p>FEN: {game.fen}</p>
                <Typography sx={{wordBreak: 'break-word', whiteSpace: 'normal'}}>
                  <p>Moves: {game.moves.join(' ')}</p>
                </Typography>
                <p>Orientation: {game.orientation}</p>
              </Paper>
            </ListItem>
          )
        )
      }
      </List>
    </ThemeProvider>
  )
}

export default App
