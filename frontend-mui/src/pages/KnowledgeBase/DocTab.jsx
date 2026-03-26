import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Pagination from '@mui/material/Pagination'

const PAGE_SIZE = 5

export default function DocTab({ kb }) {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const filtered = kb.docs.filter(d => d.name.includes(search))
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
        <Box>
          <Typography component="span" sx={{ fontSize: 13, fontWeight: 700, color: '#1e293b' }}>非結構化文件</Typography>
          <Typography component="span" sx={{ fontSize: 12, color: '#94a3b8', ml: 1 }}>上傳 PDF / Word / TXT，系統自動進行向量化索引</Typography>
        </Box>
        <Button variant="contained" size="small" sx={{ fontSize: 13 }}>↑ 上傳文件</Button>
      </Box>

      <TextField
        size="small"
        value={search}
        onChange={e => { setSearch(e.target.value); setPage(1) }}
        placeholder="搜尋檔案名稱..."
        sx={{ width: 256, mb: 1.5 }}
      />

      <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse' }}>
        <Box component="thead">
          <Box component="tr">
            {['檔案名稱', '大小', '上傳日期', '操作'].map(h => (
              <Box component="th" key={h}
                sx={{ textAlign: 'left', px: 1.5, py: 1.5, bgcolor: '#f8fafc', color: '#334155', fontWeight: 700, fontSize: 13, borderBottom: '2px solid #e2e8f0' }}>
                {h}
              </Box>
            ))}
          </Box>
        </Box>
        <Box component="tbody">
          {paged.map(doc => (
            <Box component="tr" key={doc.id}
              sx={{ borderBottom: '1px solid #f1f5f9', '&:hover': { bgcolor: '#f8fafc' } }}>
              <Box component="td" sx={{ px: 1.5, py: 1.5, fontSize: 13, color: '#334155' }}>{doc.name}</Box>
              <Box component="td" sx={{ px: 1.5, py: 1.5, fontSize: 13, color: '#64748b' }}>{doc.size}</Box>
              <Box component="td" sx={{ px: 1.5, py: 1.5, fontSize: 13, color: '#64748b' }}>{doc.uploadDate}</Box>
              <Box component="td" sx={{ px: 1.5, py: 1.5 }}>
                <Button size="small" sx={{ fontSize: 12, color: '#ef4444', fontWeight: 600, minWidth: 'unset', p: 0 }}>刪除</Button>
              </Box>
            </Box>
          ))}
        </Box>
      </Box>

      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
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
