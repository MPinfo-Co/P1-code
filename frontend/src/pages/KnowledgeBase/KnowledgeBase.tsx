import { useState } from 'react'
import { knowledgeBases } from '@/data/knowledgeBase'
import DocTab from './DocTab'
import TableTab from './TableTab'
import AccessTab from './AccessTab'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Grid from '@mui/material/Grid'
import Card from '@mui/material/Card'
import CardActionArea from '@mui/material/CardActionArea'
import Tabs from '@mui/material/Tabs'
import Tab from '@mui/material/Tab'
import MenuBookOutlinedIcon from '@mui/icons-material/MenuBookOutlined'
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined'
import './KnowledgeBase.css'

export default function KnowledgeBase() {
  const [keyword, setKeyword] = useState('')
  const [selectedKbId, setSelectedKbId] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState(0)

  const filtered = knowledgeBases.filter(
    (kb) => kb.name.includes(keyword) || kb.desc.includes(keyword)
  )

  const tabLabels = ['文件', '資料表', '存取設定']

  if (selectedKbId !== null) {
    const kb = knowledgeBases.find((k) => k.id === selectedKbId)
    if (!kb) return null
    return (
      <Box>
        <Box className="kb-detail-header">
          <Box className="kb-detail-title-wrap">
            <MenuBookOutlinedIcon className="kb-detail-icon" />
            <Typography variant="h6" className="kb-detail-title">
              {kb.name}
            </Typography>
          </Box>
          <Button
            startIcon={<ArrowBackOutlinedIcon />}
            size="small"
            onClick={() => setSelectedKbId(null)}
            className="kb-detail-back-btn"
          >
            回知識庫列表
          </Button>
        </Box>
        <Typography className="kb-detail-desc">{kb.desc}</Typography>
        <Typography className="kb-detail-partners">
          綁定夥伴：{kb.boundPartners.join('、')}
        </Typography>

        <Box className="kb-detail-tabs-bar">
          <Tabs
            value={activeTab}
            onChange={(_, v) => setActiveTab(v)}
            sx={{
              '& .MuiTab-root': { fontWeight: 600, fontSize: 13 },
              '& .Mui-selected': { color: '#2e3f6e' },
              '& .MuiTabs-indicator': { bgcolor: '#2e3f6e' },
            }}
          >
            {tabLabels.map((label) => (
              <Tab key={label} label={label} />
            ))}
          </Tabs>
        </Box>
        <Box className="kb-detail-tabs-panel">
          {activeTab === 0 && <DocTab kb={kb} />}
          {activeTab === 1 && <TableTab kb={kb} />}
          {activeTab === 2 && <AccessTab kb={kb} />}
        </Box>
      </Box>
    )
  }

  return (
    <Box>
      <Box className="kb-list-header">
        <Typography variant="h6" className="kb-list-title">
          知識庫
        </Typography>
        <Button variant="contained" size="small">
          + 新增知識庫
        </Button>
      </Box>
      <Box className="kb-list-search-wrap">
        <TextField
          size="small"
          label="關鍵字搜尋"
          placeholder="搜尋知識庫名稱或說明..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="kb-list-search"
        />
      </Box>
      <Grid container spacing={2.5}>
        {filtered.map((kb) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={kb.id}>
            <Card className="kb-card">
              <CardActionArea
                onClick={() => {
                  setSelectedKbId(kb.id)
                  setActiveTab(0)
                }}
                className="kb-card-action"
              >
                <MenuBookOutlinedIcon className="kb-card-icon" />
                <Typography className="kb-card-name">{kb.name}</Typography>
                <Typography variant="body2" className="kb-card-desc">
                  {kb.desc}
                </Typography>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
