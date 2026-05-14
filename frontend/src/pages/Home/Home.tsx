import { useNavigate } from 'react-router-dom'
import FavoriteIcon from '@mui/icons-material/Favorite'
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import CircularProgress from '@mui/material/CircularProgress'
import { useHomePartnersQuery, useFavoriteToggle } from '@/queries/useHomeQuery'
import type { PartnerItem } from '@/queries/useHomeQuery'
import './Home.css'

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
    if (!isToggling) {
      onFavoriteToggle(partner.id)
    }
  }

  return (
    <div className="partner-card" onClick={handleCardClick}>
      <button
        className="partner-card-favorite-btn"
        onClick={handleFavoriteClick}
        aria-label={partner.is_favorite ? '取消最愛' : '加入最愛'}
        type="button"
      >
        {partner.is_favorite ? (
          <FavoriteIcon sx={{ fontSize: 20, color: '#ef4444' }} />
        ) : (
          <FavoriteBorderIcon sx={{ fontSize: 20, color: '#94a3b8' }} />
        )}
      </button>
      <div className="partner-card-name">{partner.name}</div>
      {partner.description && <div className="partner-card-desc">{partner.description}</div>}
    </div>
  )
}

export default function Home() {
  const { data: partners = [], isLoading, error } = useHomePartnersQuery()
  const { mutate: toggleFavorite, isPending: isToggling } = useFavoriteToggle()

  const favoritePartners = partners.filter((p) => p.is_favorite)
  const regularPartners = partners.filter((p) => !p.is_favorite)

  if (isLoading) {
    return (
      <Box className="home-root" sx={{ display: 'flex', justifyContent: 'center', pt: 4 }}>
        <CircularProgress size={32} />
      </Box>
    )
  }

  if (error) {
    return (
      <Box className="home-root">
        <Typography className="home-empty-text">載入失敗，請重新整理頁面。</Typography>
      </Box>
    )
  }

  return (
    <Box className="home-root">
      {/* 最愛夥伴區塊：僅有最愛時顯示 */}
      {favoritePartners.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography className="home-section-title">最愛夥伴</Typography>
          <div className="home-partners-grid">
            {favoritePartners.map((partner) => (
              <PartnerCard
                key={partner.id}
                partner={partner}
                onFavoriteToggle={toggleFavorite}
                isToggling={isToggling}
              />
            ))}
          </div>
        </Box>
      )}

      {/* 夥伴區塊 */}
      <Box>
        <Typography className="home-section-title">夥伴</Typography>
        {regularPartners.length === 0 ? (
          <Typography className="home-empty-text">所有夥伴已加入最愛</Typography>
        ) : (
          <div className="home-partners-grid">
            {regularPartners.map((partner) => (
              <PartnerCard
                key={partner.id}
                partner={partner}
                onFavoriteToggle={toggleFavorite}
                isToggling={isToggling}
              />
            ))}
          </div>
        )}
      </Box>
    </Box>
  )
}
