import { useState, useRef, useEffect } from 'react'
import './App.css'

import { Button, List, ListItem, TextField, Typography } from '@mui/material'
import { ThemeProvider, createTheme } from '@mui/material/styles'

function App() {
  const theme = createTheme({
    colorSchemes: {
      dark: true,
      light: true,
    },
  })

  const [ticks, setTicks] = useState(0)
  const [pinging, setPinging] = useState(false)
  const [stream, setStream] = useState('')
  const [gameStatuses, setGameStatuses] = useState<string[]>([])

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
      setTicks(x => x + 1)
      const games = event.data.split(',')
      setGameStatuses(games)
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
    connection.current?.send(`addgame p1 p2 h8 ${stream}`)
  }

  const removeGame = () => {
    connection.current?.send('removegame 0')
  }

  return (
    <ThemeProvider theme={theme}>
      <h1>Controller</h1>
      <p>Ticks: {ticks}</p>
      <Button variant="contained" onClick={() => setPinging(x => !x)}>
      Toggle Pinging
      </Button>
      <TextField
        variant="outlined"
        value={stream}
        onChange={e => setStream(e.target.value)} />
      <Button variant="contained" onClick={() => addGame()}>Add Game</Button>
      <Button variant="contained" onClick={() => removeGame()}>Remove Game</Button>
      <div>
        <List>
          {
            Array.from(gameStatuses.entries()).map(([index, status]) => (
              <ListItem key={index}>
                <Typography>{status}</Typography>
              </ListItem>
            ))
          }
        </List>
      </div>
    </ThemeProvider>
  )
}

export default App
