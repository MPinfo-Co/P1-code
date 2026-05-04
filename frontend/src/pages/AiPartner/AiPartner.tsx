import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { aiPartners } from '@/data/aiPartners'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Grid from '@mui/material/Grid'
import Card from '@mui/material/Card'
import CardActionArea from '@mui/material/CardActionArea'
import Chip from '@mui/material/Chip'
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined'
import './AiPartner.css'

export default function AiPartner() {
  const [keyword, setKeyword] = useState('')
  const navigate = useNavigate()

  const filtered = aiPartners.filter(
    (p) => p.name.includes(keyword) || p.description?.includes(keyword)
  )

  return (
    <Box>
      <Typography variant="h6" className="ai-partner-title">
        選擇 AI 夥伴
      </Typography>

      <Box className="ai-partner-search-wrap">
        <TextField
          size="small"
          placeholder="搜尋 AI 夥伴名稱或說明..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          label="關鍵字搜尋"
          className="ai-partner-search"
        />
      </Box>

      <Grid container spacing={2.5}>
        {filtered.map((partner) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={partner.id}>
            <Card
              className="ai-partner-card"
              sx={{
                opacity: partner.disabled ? 0.5 : 1,
                pointerEvents: partner.disabled ? 'none' : 'auto',
              }}
            >
              <CardActionArea
                onClick={() => !partner.disabled && navigate(`/fn_partner/${partner.id}/issues`)}
                className="ai-partner-card-action"
              >
                <SmartToyOutlinedIcon className="ai-partner-icon" />
                <Typography className="ai-partner-name">
                  {partner.name}
                  {partner.builtin && (
                    <Chip label="預設" size="small" className="ai-partner-builtin-chip" />
                  )}
                </Typography>
                <Typography variant="body2" className="ai-partner-desc">
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
