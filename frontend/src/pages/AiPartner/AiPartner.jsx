import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { aiPartners } from '../../data/aiPartners'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Grid from '@mui/material/Grid'
import Card from '@mui/material/Card'
import CardActionArea from '@mui/material/CardActionArea'
import CardContent from '@mui/material/CardContent'
import Chip from '@mui/material/Chip'
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined'

export default function AiPartner() {
  const [keyword, setKeyword] = useState('')
  const navigate = useNavigate()

  const filtered = aiPartners.filter(
    (p) => p.name.includes(keyword) || p.description?.includes(keyword)
  )

  return (
    <Box>
      <Typography variant="h6" sx={{ fontWeight: 800, color: '#1e293b', mb: 2 }}>
        選擇 AI 夥伴
      </Typography>

      <Box
        sx={{
          bgcolor: 'white',
          borderRadius: 2,
          border: '1px solid #e2e8f0',
          p: 2,
          mb: 3,
        }}
      >
        <TextField
          size="small"
          placeholder="搜尋 AI 夥伴名稱或說明..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          label="關鍵字搜尋"
          sx={{ width: 320 }}
        />
      </Box>

      <Grid container spacing={2.5}>
        {filtered.map((partner) => (
          <Grid item xs={12} sm={6} md={4} key={partner.id}>
            <Card
              sx={{
                border: '1px solid #e2e8f0',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                opacity: partner.disabled ? 0.5 : 1,
                pointerEvents: partner.disabled ? 'none' : 'auto',
                '&:hover': {
                  transform: 'translateY(-3px)',
                  boxShadow: '0 10px 25px rgba(0,0,0,0.08)',
                },
                transition: 'all 0.3s',
              }}
            >
              <CardActionArea
                onClick={() => !partner.disabled && navigate(`/fn_partner/${partner.id}/issues`)}
                sx={{ p: 4, textAlign: 'center' }}
              >
                <SmartToyOutlinedIcon sx={{ fontSize: 48, color: '#2e3f6e', mb: 1.5 }} />
                <Typography sx={{ fontWeight: 700, color: '#1e293b', mb: 0.5 }}>
                  {partner.name}
                  {partner.builtin && (
                    <Chip
                      label="預設"
                      size="small"
                      sx={{
                        ml: 1,
                        fontSize: 11,
                        height: 20,
                        bgcolor: '#e8ebf5',
                        color: '#1e2d52',
                        fontWeight: 700,
                      }}
                    />
                  )}
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748b', mt: 1 }}>
                  {partner.description}
                </Typography>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
