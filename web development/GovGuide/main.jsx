import React from 'react'
import ReactDOM from 'react-dom/client'
import { ChakraProvider, extendTheme } from '@chakra-ui/react'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './index.css'

const theme = extendTheme({
  fonts: {
    heading: "'Outfit', sans-serif",
    body: "'Outfit', sans-serif",
  },
  styles: {
    global: {
      body: {
        bg: "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
        color: "gray.800",
      },
    },
  },
  colors: {
    brand: {
      50: '#f0e7ff',
      100: '#d4bfff',
      200: '#b794ff',
      300: '#9a69ff',
      400: '#7d3eff',
      500: '#667eea',
      600: '#5568d3',
      700: '#4451bc',
      800: '#333ba5',
      900: '#22258e',
    },
    purple: {
      50: '#faf5ff',
      100: '#f3e8ff',
      200: '#e9d5ff',
      300: '#d8b4fe',
      400: '#c084fc',
      500: '#a855f7',
      600: '#9333ea',
      700: '#7e22ce',
      800: '#6b21a8',
      900: '#581c87',
    },
    accent: {
      50: '#e0fff9',
      100: '#b3fff0',
      200: '#80ffe6',
      300: '#4dffdc',
      400: '#26ffd3',
      500: '#00f2c3',
      600: '#00d9b0',
      700: '#00bf9d',
      800: '#00a68a',
      900: '#008c77',
    }
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: 'semibold',
        borderRadius: 'lg',
      },
      variants: {
        gradient: {
          bgGradient: 'linear(to-r, brand.500, purple.500)',
          color: 'white',
          _hover: {
            bgGradient: 'linear(to-r, brand.600, purple.600)',
            transform: 'translateY(-2px)',
            boxShadow: 'lg',
          },
          _active: {
            transform: 'translateY(0)',
          },
        },
      },
    },
    Card: {
      baseStyle: {
        container: {
          borderRadius: 'xl',
          overflow: 'hidden',
        },
      },
    },
  },
  shadows: {
    outline: '0 0 0 3px rgba(102, 126, 234, 0.6)',
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ChakraProvider theme={theme}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ChakraProvider>
  </React.StrictMode>,
)