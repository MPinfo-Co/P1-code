import MuiPagination from '@mui/material/Pagination'

interface PaginationProps {
  page: number
  pageSize: number
  total: number
  totalPages?: number
  onPageChange: (page: number) => void
}

export default function Pagination({
  page,
  pageSize,
  total,
  totalPages: totalPagesProp,
  onPageChange,
}: PaginationProps) {
  const totalPages = totalPagesProp ?? (pageSize > 0 ? Math.max(1, Math.ceil(total / pageSize)) : 1)
  if (totalPages <= 1) return null

  const hasRange = Number.isFinite(total) && Number.isFinite(pageSize) && pageSize > 0
  const start = hasRange ? (page - 1) * pageSize + 1 : null
  const end = hasRange ? Math.min(page * pageSize, total) : null

  return (
    <div className="grid grid-cols-3 items-center px-4 py-3 border-t border-slate-100 text-center">
      <div className="text-sm text-slate-500 justify-self-center">
        {hasRange && (
          <>
            顯示第 <span className="font-semibold text-slate-700">{start}</span>
            <span className="mx-0.5">–</span>
            <span className="font-semibold text-slate-700">{end}</span> 筆,共{' '}
            <span className="font-semibold text-slate-700">{total}</span> 筆
          </>
        )}
      </div>
      <div className="justify-self-center">
        <MuiPagination
          count={totalPages}
          page={page}
          onChange={(_, p) => onPageChange(p)}
          color="primary"
          shape="rounded"
          siblingCount={1}
          boundaryCount={1}
        />
      </div>
      <div />
    </div>
  )
}
