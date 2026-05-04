import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import type { KnowledgeBase } from '@/data/knowledgeBase'
import './TableTab.css'

interface Props {
  kb: KnowledgeBase
}

export default function TableTab({ kb }: Props) {
  const [selectedTableId, setSelectedTableId] = useState<string | null>(null)

  if (selectedTableId) {
    const table = kb.tables.find((t) => t.id === selectedTableId)
    if (!table) return null
    return (
      <Box>
        <Box className="table-tab-detail-header">
          <Typography className="table-tab-detail-title">{table.name}</Typography>
          <Button
            size="small"
            onClick={() => setSelectedTableId(null)}
            className="table-tab-back-btn"
          >
            ← 回列表
          </Button>
        </Box>
        <Box className="table-tab-scroll">
          <Box component="table" className="table-tab-table">
            <Box component="thead">
              <Box component="tr">
                {table.columns.map((col) => (
                  <Box component="th" key={col} className="table-tab-th">
                    {col}
                  </Box>
                ))}
              </Box>
            </Box>
            <Box component="tbody">
              {table.rows.map((row, i) => (
                <Box component="tr" key={i} className="table-tab-tr">
                  {row.map((cell, j) => (
                    <Box component="td" key={j} className="table-tab-td">
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
      <Box className="table-tab-list-header">
        <Box>
          <Typography component="span" className="table-tab-list-title">
            結構化資料表
          </Typography>
          <Typography component="span" className="table-tab-list-subtitle">
            可自訂建立或匯入 Excel/CSV
          </Typography>
        </Box>
        <Button variant="contained" size="small" className="table-tab-add-btn">
          + 新增資料表
        </Button>
      </Box>
      <Box className="table-tab-list">
        {kb.tables.map((table) => (
          <Box
            key={table.id}
            onClick={() => setSelectedTableId(table.id)}
            className="table-tab-card"
          >
            <Box>
              <Typography className="table-tab-card-name">{table.name}</Typography>
              <Typography className="table-tab-card-meta">
                {table.columns.length} 欄 · {table.rows.length} 筆 · 建立 {table.createdDate}
              </Typography>
            </Box>
            <Typography className="table-tab-card-arrow">→</Typography>
          </Box>
        ))}
      </Box>
    </Box>
  )
}
