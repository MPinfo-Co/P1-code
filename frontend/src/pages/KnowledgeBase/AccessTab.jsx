import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'

export default function AccessTab({ kb }) {
  return (
    <Box>
      <Typography sx={{ fontWeight: 700, color: '#1e293b', fontSize: 13, mb: 2 }}>
        存取設定
      </Typography>
      <Typography sx={{ fontSize: 13, color: '#64748b', mb: 1.5 }}>
        以下角色可存取此知識庫：
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {kb.accessRoles.map((role) => (
          <Box
            key={role}
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              border: '1px solid #e2e8f0',
              borderRadius: 1,
              px: 2,
              py: 1.5,
            }}
          >
            <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#334155' }}>{role}</Typography>
            <Button
              size="small"
              sx={{ fontSize: 12, color: '#ef4444', fontWeight: 600, minWidth: 'unset', p: 0 }}
            >
              移除
            </Button>
          </Box>
        ))}
      </Box>
      <Button
        variant="outlined"
        size="small"
        sx={{
          mt: 2,
          fontSize: 13,
          fontWeight: 600,
          borderColor: '#2e3f6e',
          color: '#2e3f6e',
          '&:hover': { bgcolor: '#eef1f8', borderColor: '#2e3f6e' },
        }}
      >
        + 新增角色存取
      </Button>
    </Box>
  )
}
