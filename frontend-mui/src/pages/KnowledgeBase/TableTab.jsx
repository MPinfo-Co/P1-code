import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'

export default function TableTab({ kb }) {
  const [selectedTableId, setSelectedTableId] = useState(null)

  if (selectedTableId) {
    const table = kb.tables.find(t => t.id === selectedTableId)
    return (
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography sx={{ fontWeight: 700, color: '#1e293b' }}>{table.name}</Typography>
          <Button size="small" onClick={() => setSelectedTableId(null)}
            sx={{ fontSize: 13, color: '#64748b', fontWeight: 600 }}>
            ← 回列表
          </Button>
        </Box>
        <Box sx={{ overflowX: 'auto' }}>
          <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <Box component="thead">
              <Box component="tr">
                {table.columns.map(col => (
                  <Box component="th" key={col}
                    sx={{ px: 1.5, py: 1.5, bgcolor: '#f8fafc', color: '#334155', fontWeight: 700, border: '1px solid #e2e8f0', textAlign: 'left' }}>
                    {col}
                  </Box>
                ))}
              </Box>
            </Box>
            <Box component="tbody">
              {table.rows.map((row, i) => (
                <Box component="tr" key={i} sx={{ '&:hover': { bgcolor: '#f8fafc' } }}>
                  {row.map((cell, j) => (
                    <Box component="td" key={j}
                      sx={{ px: 1.5, py: 1.5, border: '1px solid #e2e8f0', color: '#475569' }}>
                      {cell}
                    </Box>
                  ))}
                </Box>
              ))}
            </Box>
          </Box>
        </Box>
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography component="span" sx={{ fontWeight: 700, color: '#1e293b', fontSize: 13 }}>結構化資料表</Typography>
          <Typography component="span" sx={{ fontSize: 12, color: '#94a3b8', ml: 1 }}>可自訂建立或匯入 Excel/CSV</Typography>
        </Box>
        <Button variant="contained" size="small" sx={{ fontSize: 13 }}>+ 新增資料表</Button>
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {kb.tables.map(table => (
          <Box
            key={table.id}
            onClick={() => setSelectedTableId(table.id)}
            sx={{
              border: '1px solid #e2e8f0',
              borderRadius: 1,
              p: 2,
              cursor: 'pointer',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              '&:hover': { bgcolor: '#f8fafc' },
              transition: 'background-color 0.2s',
            }}
          >
            <Box>
              <Typography sx={{ fontWeight: 600, color: '#1e293b', fontSize: 13 }}>{table.name}</Typography>
              <Typography sx={{ fontSize: 12, color: '#94a3b8', mt: 0.5 }}>
                {table.columns.length} 欄 · {table.rows.length} 筆 · 建立 {table.createdDate}
              </Typography>
            </Box>
            <Typography sx={{ color: '#94a3b8', fontSize: 13 }}>→</Typography>
          </Box>
        ))}
      </Box>
    </Box>
  )
}
