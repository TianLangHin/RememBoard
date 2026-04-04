import { useState, useRef, useEffect } from 'react'
import './App.css'

import { getMoveList } from './utils/movelist.ts'
import { type ServerPayload, parseServerPayload } from './utils/parse.ts'

import { Chessboard } from 'react-chessboard'
import {
  Box, Button, Drawer, Grid, List, ListItem, Paper, Typography
} from '@mui/material'
import { ThemeProvider, createTheme } from '@mui/material/styles'

function App() {
  const theme = createTheme({
    colorSchemes: {
      dark: true,
      light: true,
    },
  })

  // Main state being stored by the client. This is sent from the server.
  const [gameInfo, setGameInfo] = useState<ServerPayload[]>([])

  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  const selectedGame = selectedIndex === null ? null : gameInfo[selectedIndex]

  const defaultFen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
  const chessboardSettings = {
    position: selectedGame?.fen ?? defaultFen,
    allowDragging: false,
  }

  const scrollRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const element = scrollRef.current
    if (element) {
      element.scrollTop = element.scrollHeight
    }
  }, [gameInfo, selectedIndex])

  // Upon startup, establish the websocket connection.
  const connection = useRef<WebSocket | null>(null)
  useEffect(() => {
    const socket = new WebSocket('ws://localhost:19941')
    socket.addEventListener('open', _ => {
      // Signal to the server this is a client.
      socket.send('client')
    })
    // For debugging only.
    socket.addEventListener('close', _ => {
      console.log('closed')
    })
    // The main processing to conduct.
    socket.addEventListener('message', event => {
      const gamePayloads = event.data.split(',')
      const parsedPayloads = gamePayloads
        .map((payload: string) => parseServerPayload(payload))
        .filter((payload: ServerPayload | null) => payload !== null)
      setGameInfo(parsedPayloads)
    })
    connection.current = socket
    return () => connection.current?.close()
  }, [])

  return (
    <ThemeProvider theme={theme}>
      <Drawer
        open={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        PaperProps={{sx: {width: 1/5}}}>
        <Box role="presentation">
          <List>
          {
            Array.from(gameInfo.entries()).map(
              ([index, game]) => (
                <ListItem key={index}>
                  <Grid container spacing={1}>
                    <Grid size={8}>
                      <Chessboard options={{position: game.fen, allowDragging: false}} />
                    </Grid>
                    <Grid size={4}>
                      <Button variant="contained" onClick={() => setSelectedIndex(index)}>Select Game</Button>
                    </Grid>
                  </Grid>
                </ListItem>
              )
            )
          }
          </List>
        </Box>
      </Drawer>
      {/* Main content. */}
      <Grid container spacing={2} sx={{width: '100%'}}>
        {/* Row 1. */}
        <Grid size={12}>
          <Paper sx={{height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <h1>RememBoard</h1>
          </Paper>
        </Grid>
        {/* Row 2. */}
        <Grid size={4}>
          <Paper sx={{height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <h2>White Player: {selectedGame?.player1 ?? 'None'}</h2>
          </Paper>
        </Grid>
        <Grid size={4} sx={{display: 'flex'}}>
          <Paper sx={{height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <h2>Black Player: {selectedGame?.player2 ?? 'None'}</h2>
          </Paper>
        </Grid>
        <Grid size={2} sx={{display: 'flex'}}>
          <Paper sx={{height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <h3>Viewing Game: {selectedIndex ?? 'None'}</h3>
          </Paper>
        </Grid>
        <Grid size={2} sx={{display: 'flex'}}>
          <Button
            variant="contained"
            style={{'height': '100%'}}
            onClick={() => setIsDrawerOpen(true)}>
            Open Drawer
          </Button>
        </Grid>
        {/* Row 3. */}
        <Grid size={12}>
          <div style={{display: 'flex'}}>
            {/* The first column shows the image transmitted from the server. */}
            <div style={{flex: 1, aspectRatio: 1}}>
              <Chessboard options={chessboardSettings} />
            </div>
            <div ref={scrollRef} style={{flex: 1, overflow: 'scroll', height: '100%'}}>
            {
              getMoveList(selectedGame?.moves ?? []).map(({moveNum, white, black}) => (
                <Typography key={moveNum}>{`${moveNum}. ${white} ${black}`}</Typography>
              ))
            }
            </div>
          </div>
        </Grid>
        <Grid size={12}>
          <img src={'data:image/png;base64,' + (selectedGame?.imageContent ?? '')} width="60%" />
        </Grid>
      </Grid>
    </ThemeProvider>
  )
}

export default App
