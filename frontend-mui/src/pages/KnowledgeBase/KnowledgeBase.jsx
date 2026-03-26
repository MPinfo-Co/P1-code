import { useState } from 'react'
import { knowledgeBases } from '../../data/knowledgeBase'
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

export default function KnowledgeBase() {
  const [keyword, setKeyword] = useState('')
  const [selectedKbId, setSelectedKbId] = useState(null)
  const [activeTab, setActiveTab] = useState(0)

  const filtered = knowledgeBases.filter(
    kb => kb.name.includes(keyword) || kb.desc.includes(keyword)
  )

  const tabLabels = ['文件', '資料表', '存取設定']

  if (selectedKbId !== null) {
    const kb = knowledgeBases.find(k => k.id === selectedKbId)
    return (
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <MenuBookOutlinedIcon sx={{ color: '#64748b' }} />
            <Typography variant="h6" sx={{ fontWeight: 800, color: '#1e293b' }}>{kb.name}</Typography>
          </Box>
          <Button startIcon={<ArrowBackOutlinedIcon />} size="small"
            onClick={() => setSelectedKbId(null)}
            sx={{ color: '#64748b', fontWeight: 600 }}>
            回知識庫列表
          </Button>
        </Box>
        <Typography sx={{ fontSize: 13, color: '#64748b', mb: 0.5 }}>{kb.desc}</Typography>
        <Typography sx={{ fontSize: 12, color: '#2e3f6e', fontWeight: 600, mb: 3 }}>
          綁定夥伴：{kb.boundPartners.join('、')}
        </Typography>

        <Box sx={{ borderBottom: '1px solid #e2e8f0' }}>
          <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}
            sx={{ '& .MuiTab-root': { fontWeight: 600, fontSize: 13 }, '& .Mui-selected': { color: '#2e3f6e' }, '& .MuiTabs-indicator': { bgcolor: '#2e3f6e' } }}>
            {tabLabels.map(label => <Tab key={label} label={label} />)}
          </Tabs>
        </Box>
        <Box sx={{ bgcolor: 'white', border: '1px solid #e2e8f0', borderTop: 'none', borderRadius: '0 0 8px 8px', p: 3 }}>
          {activeTab === 0 && <DocTab kb={kb} />}
          {activeTab === 1 && <TableTab kb={kb} />}
          {activeTab === 2 && <AccessTab kb={kb} />}
        </Box>
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 800, color: '#1e293b' }}>知識庫</Typography>
        <Button variant="contained" size="small">+ 新增知識庫</Button>
      </Box>
      <Box sx={{ bgcolor: 'white', borderRadius: 2, border: '1px solid #e2e8f0', p: 2, mb: 3 }}>
        <TextField size="small" label="關鍵字搜尋" placeholder="搜尋知識庫名稱或說明..."
          value={keyword} onChange={e => setKeyword(e.target.value)} sx={{ width: 320 }} />
      </Box>
      <Grid container spacing={2.5}>
        {filtered.map(kb => (
          <Grid item xs={12} sm={6} md={4} key={kb.id}>
            <Card sx={{ border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', '&:hover': { transform: 'translateY(-3px)', boxShadow: '0 10px 25px rgba(0,0,0,0.08)' }, transition: 'all 0.3s' }}>
              <CardActionArea onClick={() => { setSelectedKbId(kb.id); setActiveTab(0) }} sx={{ p: 4, textAlign: 'center' }}>
                <MenuBookOutlinedIcon sx={{ fontSize: 48, color: '#2e3f6e', mb: 2 }} />
                <Typography sx={{ fontWeight: 700, color: '#1e293b' }}>{kb.name}</Typography>
                <Typography variant="body2" sx={{ color: '#64748b', mt: 1 }}>{kb.desc}</Typography>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
