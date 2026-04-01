import { useState, useRef, useEffect } from 'react'
import './App.css'

import { Typography } from '@mui/material'
import { ThemeProvider, createTheme } from '@mui/material/styles'

function App() {
  const theme = createTheme({
    colorSchemes: {
      dark: true,
      light: true,
    },
  })

  const [fens, setFens] = useState<string[]>([])
  const [images, setImages] = useState<string[]>([])

  const connection = useRef<WebSocket | null>(null)
  useEffect(() => {
    const socket = new WebSocket('ws://localhost:19941')
    socket.addEventListener('open', _ => {
      socket.send('client')
    })
    socket.addEventListener('close', _ => {
      console.log('closed')
    })
    socket.addEventListener('message', event => {
      var newImages: string[] = []
      var newFens: string[] = []
      const processedImages = event.data.split(',')
      for (const data of processedImages) {
        const d = data.split('|')
        newImages.push(d[0])
        newImages.push(d[1])
      }
      setFens(newFens)
      setImages(newImages)
    })
    connection.current = socket
    return () => connection.current?.close()
  }, [])

  return (
    <ThemeProvider theme={theme}>
      <h1>Client</h1>
      <div style={{display: 'flex'}}>
        {
          Array.from(images.entries()).map(([index, image]) => (
            <div style={{flex: 1}} key={index}>
              <img src={'data:image/png;base64,' + image} width="640px" height="360px" />
            </div>
          ))
        }
      </div>
        {
          Array.from(fens.entries()).map(([index, fen]) => (
            <Typography key={index}>{fen}</Typography>
          ))
        }
      <div>
      </div>
    </ThemeProvider>
  )
}

export default App
