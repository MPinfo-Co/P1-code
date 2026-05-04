import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Pagination from '@mui/material/Pagination'
import type { KnowledgeBase } from '@/data/knowledgeBase'
import './DocTab.css'

const PAGE_SIZE = 5

interface Props {
  kb: KnowledgeBase
}

export default function DocTab({ kb }: Props) {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const filtered = kb.docs.filter((d) => d.name.includes(search))
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <Box>
      <Box className="doc-tab-header">
        <Box>
          <Typography component="span" className="doc-tab-title">
            非結構化文件
          </Typography>
          <Typography component="span" className="doc-tab-subtitle">
            上傳 PDF / Word / TXT，系統自動進行向量化索引
          </Typography>
        </Box>
        <Button variant="contained" size="small" className="doc-tab-action-btn">
          ↑ 上傳文件
        </Button>
      </Box>

      <TextField
        size="small"
        value={search}
        onChange={(e) => {
          setSearch(e.target.value)
          setPage(1)
        }}
        placeholder="搜尋檔案名稱..."
        className="doc-tab-search"
      />

      <Box component="table" className="doc-tab-table">
        <Box component="thead">
          <Box component="tr">
            {['檔案名稱', '大小', '上傳日期', '操作'].map((h) => (
              <Box component="th" key={h} className="doc-tab-th">
                {h}
              </Box>
            ))}
          </Box>
        </Box>
        <Box component="tbody">
          {paged.map((doc) => (
            <Box component="tr" key={doc.id} className="doc-tab-tr">
              <Box component="td" className="doc-tab-td">
                {doc.name}
              </Box>
              <Box component="td" className="doc-tab-td-muted">
                {doc.size}
              </Box>
              <Box component="td" className="doc-tab-td-muted">
                {doc.uploadDate}
              </Box>
              <Box component="td" className="doc-tab-td-action">
                <Button size="small" className="doc-tab-delete-btn">
                  刪除
                </Button>
              </Box>
            </Box>
          ))}
        </Box>
      </Box>

      {totalPages > 1 && (
        <Box className="doc-tab-pagination-wrap">
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_, v) => setPage(v)}
            size="small"
            sx={{ '& .Mui-selected': { bgcolor: '#2e3f6e', color: 'white' } }}
          />
        </Box>
      )}
    </Box>
  )
}
