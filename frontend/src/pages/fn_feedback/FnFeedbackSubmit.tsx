// src/pages/fn_feedback/FnFeedbackSubmit.tsx
import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Alert from '@mui/material/Alert'
import CircularProgress from '@mui/material/CircularProgress'
import StarIcon from '@mui/icons-material/Star'
import StarBorderIcon from '@mui/icons-material/StarBorder'
import { useSubmitFeedback } from '@/queries/useFeedbackQuery'
import './FnFeedbackSubmit.css'

export default function FnFeedbackSubmit() {
  const [rating, setRating] = useState<number | null>(null)
  const [hoverRating, setHoverRating] = useState<number | null>(null)
  const [comment, setComment] = useState('')
  const [ratingError, setRatingError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const submitFeedback = useSubmitFeedback()

  function handleStarClick(value: number) {
    setRating(value)
    setRatingError(null)
  }

  function handleSubmit() {
    setSuccessMessage(null)
    if (!rating) {
      setRatingError('請選擇評分')
      return
    }
    const payload = comment.trim() ? { rating, comment: comment.trim() } : { rating }
    submitFeedback.mutate(payload, {
      onSuccess: () => {
        setSuccessMessage('感謝您的回饋！')
        setRating(null)
        setComment('')
        setRatingError(null)
      },
    })
  }

  const displayRating = hoverRating ?? rating ?? 0

  return (
    <Box className="fn-feedback-submit-container">
      <Typography variant="h6" className="fn-feedback-submit-title">
        提交使用回饋
      </Typography>

      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {successMessage}
        </Alert>
      )}

      <Box className="fn-feedback-submit-form">
        {/* 評分 */}
        <Box className="fn-feedback-field">
          <Typography className="fn-feedback-field-label">
            評分 <span className="fn-feedback-required">*</span>
          </Typography>
          <Box className="fn-feedback-stars" onMouseLeave={() => setHoverRating(null)}>
            {[1, 2, 3, 4, 5].map((value) =>
              displayRating >= value ? (
                <StarIcon
                  key={value}
                  className="fn-feedback-star fn-feedback-star--filled"
                  onClick={() => handleStarClick(value)}
                  onMouseEnter={() => setHoverRating(value)}
                />
              ) : (
                <StarBorderIcon
                  key={value}
                  className="fn-feedback-star fn-feedback-star--empty"
                  onClick={() => handleStarClick(value)}
                  onMouseEnter={() => setHoverRating(value)}
                />
              )
            )}
          </Box>
          {ratingError && <Typography className="fn-feedback-error">{ratingError}</Typography>}
        </Box>

        {/* 留言 */}
        <Box className="fn-feedback-field">
          <Typography className="fn-feedback-field-label">留言</Typography>
          <textarea
            className="fn-feedback-textarea"
            placeholder="請輸入您的建議或心得…"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={4}
          />
        </Box>

        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={submitFeedback.isPending}
          className="fn-feedback-submit-btn"
        >
          {submitFeedback.isPending ? <CircularProgress size={18} color="inherit" /> : '提交'}
        </Button>
      </Box>
    </Box>
  )
}
