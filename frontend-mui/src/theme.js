import { createTheme } from '@mui/material/styles'

const theme = createTheme({
  palette: {
    primary: {
      main: '#2e3f6e',
      dark: '#1e2d52',
    },
  },
  shape: {
    borderRadius: 8,
  },
  typography: {
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft JhengHei', sans-serif",
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 700,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: '#f8fafc',
          },
        },
      },
    },
    MuiDataGrid: {
      styleOverrides: {
        columnHeader: {
          backgroundColor: '#f1f5f9',
          fontWeight: 800,
          color: '#1e293b',
          fontSize: 14,
        },
        root: {
          border: 'none',
          '& .MuiDataGrid-row:hover': {
            backgroundColor: '#f8fafc',
          },
        },
      },
    },
  },
})

export default theme
