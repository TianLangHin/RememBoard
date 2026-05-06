import { useState, useRef, useEffect } from 'react'
import './App.css'

import {
  type ServerPayload, parseServerPayload,
  type StoredGame, parseStoredGame
} from './utils/parse.ts'

import {
  Button, Drawer, FormControl, Grid, InputLabel,
  List, ListItem, MenuItem, Paper, Select, TextField, Typography
} from '@mui/material'

import { ThemeProvider, createTheme } from '@mui/material/styles'

function App() {
  const theme = createTheme({
    colorSchemes: {
      dark: true,
      light: true,
    },
  })

  const [pings, setPings] = useState<number[]>([0, 0])
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
  const [modelType, setModelType] = useState('wooden-yolo')
  const [conclusion, setConclusion] = useState('*')

  // Toggles whether the persistent game retrieval functionality is being used.
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  // TextFields for the panel where games can be manipulated in persistent storage.
  const [gameFindId, setGameFindId] = useState(0)
  const [findDate, setFindDate] = useState('')
  const [findWhite, setFindWhite] = useState('')
  const [findBlack, setFindBlack] = useState('')
  const [findResult, setFindResult] = useState('')
  const [gameDeleteId, setGameDeleteId] = useState(0)

  // Also for displaying the results.
  const [queryResults, setQueryResults] = useState<StoredGame[]>([])

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
      setPings(p => [p[1], Date.now()])

      const gamePayloads = event.data.split('%')
      const parsedPayloads = gamePayloads
        .map((payload: string) => parseServerPayload(payload))
        .filter((payload: ServerPayload | null) => payload !== null)

      if (parsedPayloads.length > 0) {
        setGameInfo(parsedPayloads)
        if (pinging) {
          connection.current?.send('inference')
        }
      } else {
        const storagePayloads = gamePayloads
          .map((payload: string) => parseStoredGame(payload))
          .filter((game: StoredGame | null) => game !== null)
        setQueryResults(storagePayloads)
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
    connection.current?.send(`addgame "${playerOne}" "${playerTwo}" ${orientation} ${stream} ${modelType}`)
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
    connection.current?.send(`renameplayers ${selectedGame} "${playerOne}" "${playerTwo}"`)
  }

  const reorientGame = () => {
    connection.current?.send(`reorient ${selectedGame} ${orientation}`)
  }

  const registerConclusion = () => {
    connection.current?.send(`conclude ${selectedGame} ${conclusion}`)
  }

  const insertGame = () => {
    connection.current?.send(`storage insert ${selectedGame}`)
  }

  const findGame = () => {
    connection.current?.send(`storage find ${gameFindId}`)
  }

  const searchGames = () => {
    connection.current?.send(`storage search "${findDate}" "${findWhite}" "${findBlack}" "${findResult}"`)
  }

  const deleteGame = () => {
    connection.current?.send(`storage delete ${gameDeleteId}`)
  }

  return (
    <ThemeProvider theme={theme}>
      <Drawer
        open={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        PaperProps={{sx: {width: 3/4}}}>
        <Paper sx={{p: 5, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <h2>Stored Game Management</h2>
        </Paper>
        <Grid container spacing={2} sx={{p: 5}}>
          {/* Row. */}
          <Grid size={8} sx={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <TextField
              variant="outlined"
              label="Searching Game ID"
              value={gameFindId}
              onChange={e => setGameFindId(Number(e.target.value))}
              />
          </Grid>
          <Grid size={4} sx={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <Button variant="contained" onClick={findGame}>Find Game</Button>
          </Grid>
          {/* Row. */}
          <Grid size={2} sx={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <TextField
              variant="outlined"
              label="Date"
              value={findDate}
              onChange={e => setFindDate(e.target.value)}
              />
          </Grid>
          <Grid size={2} sx={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <TextField
              variant="outlined"
              label="White Player"
              value={findWhite}
              onChange={e => setFindWhite(e.target.value)}
              />
          </Grid>
          <Grid size={2} sx={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <TextField
              variant="outlined"
              label="Black Player"
              value={findBlack}
              onChange={e => setFindBlack(e.target.value)}
              />
          </Grid>
          <Grid size={2} sx={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <TextField
              variant="outlined"
              label="Game Result"
              value={findResult}
              onChange={e => setFindResult(e.target.value)}
              />
          </Grid>
          <Grid size={4} sx={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <Button variant="contained" onClick={searchGames}>Search for Games</Button>
          </Grid>
          {/* Row. */}
          <Grid size={8} sx={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <TextField
              variant="outlined"
              label="Deleting Game ID"
              value={gameDeleteId}
              onChange={e => setGameDeleteId(Number(e.target.value))}
              />
          </Grid>
          <Grid size={4} sx={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <Button variant="contained" onClick={deleteGame}>Delete Game</Button>
          </Grid>
          {/* Row. */}
          <List>
            {
              Array.from(queryResults.entries()).map(
                ([index, queryResult]) => (
                  <ListItem key={index}>
                    <Paper>
                      <h3>Game ID: {queryResult.id}</h3>
                      <p><b>Date:</b> {queryResult.date}</p>
                      <p><b>White Player:</b> {queryResult.white}</p>
                      <p><b>Black Player:</b> {queryResult.black}</p>
                      <p><b>Result:</b> {queryResult.result}</p>
                      <p><b>Moves:</b> {queryResult.moves}</p>
                    </Paper>
                  </ListItem>
                )
              )
            }
          </List>
        </Grid>
      </Drawer>
      <Grid container spacing={2} sx={{width: '100%'}}>
        {/* Row 1. */}
        <Grid size={12}>
          <Paper sx={{height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <h1>RememBoard Controller</h1>
          </Paper>
        </Grid>
        <Grid size={12}>
          <Paper>
            <Button variant="contained" onClick={() => setIsDrawerOpen(true)}>
              Search Games
            </Button>
          </Paper>
        </Grid>
        {/* Row 2. */}
        <Grid size={12}>
          <Paper elevation={2}>
            <Grid container sx={{width: '100%', p: 2}}>
              <Grid size={4}>
                <p>FPS: {pings[0] === pings[1] ? 0 : (1000 / (pings[1] - pings[0])).toFixed(2)}</p>
              </Grid>
              <Grid size={4}>
                <p>Currently Pinging: {pinging ? 'True' : 'False'}</p>
              </Grid>
              <Grid size={4}>
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
              <Grid size={3}>
                <FormControl>
                  <InputLabel>Top-Left Corner</InputLabel>
                  <Select
                    value={modelType}
                    defaultValue={'wooden-yolo'}
                    label="Model Type"
                    onChange={e => setModelType(e.target.value)}>
                    <MenuItem value={'wooden-yolo'}>Wooden (YOLO)</MenuItem>
                    <MenuItem value={'handheld-yolo'}>Handheld (YOLO)</MenuItem>
                    <MenuItem value={'wooden-rtdetr'}>Wooden (RTDETR)</MenuItem>
                    <MenuItem value={'handheld-rtdetr'}>Handheld (RTDETR)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={3}>
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
                <FormControl sx={{width: '40%'}}>
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
              {/* Row. */}
              <Grid size={6}>
                <FormControl sx={{width: '40%'}}>
                  <InputLabel>Game Result</InputLabel>
                  <Select
                    value={conclusion}
                    defaultValue={'*'}
                    label="Game Result"
                    onChange={e => setConclusion(e.target.value)}>
                    <MenuItem value={'*'}>Unconcluded</MenuItem>
                    <MenuItem value={'1/2-1/2'}>Draw</MenuItem>
                    <MenuItem value={'1-0'}>White Win</MenuItem>
                    <MenuItem value={'0-1'}>Black Win</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={6}>
                <Button variant="contained" onClick={registerConclusion} sx={{height: '100%'}}>Register Conclusion</Button>
              </Grid>
              {/* Row 4e. */}
              <Grid size={3}>
                <Button variant="contained" onClick={pauseGame}>Pause Game</Button>
              </Grid>
              <Grid size={3}>
                <Button variant="contained" onClick={unpauseGame}>Unpause Game</Button>
              </Grid>
              <Grid size={6}>
                <Button variant="contained" onClick={insertGame}>Save Game</Button>
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
