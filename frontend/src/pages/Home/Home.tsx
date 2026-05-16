import { useNavigate } from 'react-router-dom'
import FavoriteIcon from '@mui/icons-material/Favorite'
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder'
import AdbIcon from '@mui/icons-material/Adb'
import TableChartIcon from '@mui/icons-material/TableChart'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import CircularProgress from '@mui/material/CircularProgress'
import { useHomePartnersQuery, useHomeTablesQuery, useFavoriteToggle } from '@/queries/useHomeQuery'
import type { PartnerItem, TableItem } from '@/queries/useHomeQuery'
import './Home.css'

// ─── Partner Card ─────────────────────────────────────────────────────────────

interface PartnerCardProps {
  partner: PartnerItem
  onFavoriteToggle: (partnerId: number) => void
  isToggling: boolean
}

function PartnerCard({ partner, onFavoriteToggle, isToggling }: PartnerCardProps) {
  const navigate = useNavigate()

  function handleCardClick() {
    navigate(`/ai_partner_chat?partnerId=${partner.id}`)
  }

  function handleFavoriteClick(e: React.MouseEvent) {
    e.stopPropagation()
    if (!isToggling) onFavoriteToggle(partner.id)
  }

  return (
    <div className="partner-card-wrapper" onClick={handleCardClick}>
      <div className={`partner-card${partner.is_favorite ? ' favorite' : ''}`}>
        <button
          className={`partner-card-favorite-btn${partner.is_favorite ? ' active' : ''}`}
          onClick={handleFavoriteClick}
          aria-label={partner.is_favorite ? '取消最愛' : '加入最愛'}
          type="button"
        >
          {partner.is_favorite ? (
            <FavoriteIcon sx={{ fontSize: 14 }} />
          ) : (
            <FavoriteBorderIcon sx={{ fontSize: 14 }} />
          )}
        </button>
        <div className="partner-card-icon">
          <AdbIcon sx={{ fontSize: 48 }} />
        </div>
        {partner.description && (
          <div className="partner-card-desc--hover">{partner.description}</div>
        )}
      </div>
      <div className="partner-card-name">{partner.name}</div>
    </div>
  )
}

// ─── Table Card ───────────────────────────────────────────────────────────────

interface TableCardProps {
  table: TableItem
  onFavoriteToggle: (tableId: number) => void
  isToggling: boolean
}

function TableCard({ table, onFavoriteToggle, isToggling }: TableCardProps) {
  const navigate = useNavigate()

  function handleCardClick() {
    navigate(`/custom_table_data_input?tableId=${table.id}`)
  }

  function handleFavoriteClick(e: React.MouseEvent) {
    e.stopPropagation()
    if (!isToggling) onFavoriteToggle(table.id)
  }

  return (
    <div className="table-card-wrapper" onClick={handleCardClick}>
      <div className={`table-card${table.is_favorite ? ' favorite' : ''}`}>
        <button
          className={`table-card-favorite-btn${table.is_favorite ? ' active' : ''}`}
          onClick={handleFavoriteClick}
          aria-label={table.is_favorite ? '取消最愛' : '加入最愛'}
          type="button"
        >
          {table.is_favorite ? (
            <FavoriteIcon sx={{ fontSize: 14 }} />
          ) : (
            <FavoriteBorderIcon sx={{ fontSize: 14 }} />
          )}
        </button>
        <div className="table-card-icon">
          <TableChartIcon sx={{ fontSize: 48 }} />
        </div>
        {table.description && <div className="table-card-desc--hover">{table.description}</div>}
      </div>
      <div className="table-card-name">{table.name}</div>
    </div>
  )
}

// ─── Home ─────────────────────────────────────────────────────────────────────

type FavoriteItem = { kind: 'partner'; data: PartnerItem } | { kind: 'table'; data: TableItem }

export default function Home() {
  const {
    data: partners = [],
    isLoading: partnersLoading,
    error: partnersError,
  } = useHomePartnersQuery()
  const { data: tables = [], isLoading: tablesLoading } = useHomeTablesQuery()
  const { mutate: toggleFavorite, isPending: isToggling } = useFavoriteToggle()

  const isLoading = partnersLoading || tablesLoading

  const favoriteItems: FavoriteItem[] = [
    ...partners
      .filter((p) => p.is_favorite)
      .map((p): FavoriteItem => ({ kind: 'partner', data: p })),
    ...tables.filter((t) => t.is_favorite).map((t): FavoriteItem => ({ kind: 'table', data: t })),
  ].sort((a, b) => a.data.sort_order - b.data.sort_order)

  const regularPartners = partners.filter((p) => !p.is_favorite)
  const regularTables = tables.filter((t) => !t.is_favorite)

  if (isLoading) {
    return (
      <Box className="home-root" sx={{ display: 'flex', justifyContent: 'center', pt: 4 }}>
        <CircularProgress size={32} />
      </Box>
    )
  }

  if (partnersError) {
    return (
      <Box className="home-root">
        <Typography className="home-empty-text">載入失敗，請重新整理頁面。</Typography>
      </Box>
    )
  }

  return (
    <Box className="home-root">
      {/* 最愛 */}
      {favoriteItems.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography className="home-section-title">最愛</Typography>
          <div className="home-partners-grid">
            {favoriteItems.map((item) =>
              item.kind === 'partner' ? (
                <PartnerCard
                  key={`partner-${item.data.id}`}
                  partner={item.data}
                  onFavoriteToggle={(id) => toggleFavorite({ item_type: 'partner', item_id: id })}
                  isToggling={isToggling}
                />
              ) : (
                <TableCard
                  key={`table-${item.data.id}`}
                  table={item.data}
                  onFavoriteToggle={(id) => toggleFavorite({ item_type: 'table', item_id: id })}
                  isToggling={isToggling}
                />
              )
            )}
          </div>
        </Box>
      )}

      {/* 夥伴 */}
      <Box sx={{ mb: 4 }}>
        <Typography className="home-section-title">夥伴</Typography>
        {regularPartners.length === 0 ? (
          <Typography className="home-empty-text">所有夥伴已加入最愛</Typography>
        ) : (
          <div className="home-partners-grid">
            {regularPartners.map((partner) => (
              <PartnerCard
                key={partner.id}
                partner={partner}
                onFavoriteToggle={(id) => toggleFavorite({ item_type: 'partner', item_id: id })}
                isToggling={isToggling}
              />
            ))}
          </div>
        )}
      </Box>

      {/* 資料 */}
      {tables.length > 0 && (
        <Box>
          <Typography className="home-section-title">資料</Typography>
          {regularTables.length === 0 ? (
            <Typography className="home-empty-text">所有資料表已加入最愛</Typography>
          ) : (
            <div className="home-partners-grid">
              {regularTables.map((table) => (
                <TableCard
                  key={table.id}
                  table={table}
                  onFavoriteToggle={(id) => toggleFavorite({ item_type: 'table', item_id: id })}
                  isToggling={isToggling}
                />
              ))}
            </div>
          )}
        </Box>
      )}
    </Box>
  )
}
