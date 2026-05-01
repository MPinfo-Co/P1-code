// src/pages/fn_dept/FnDeptMembers.tsx
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'
import Divider from '@mui/material/Divider'
import { useDeptMembersQuery } from '@/queries/useDeptQuery'

interface Props {
  open: boolean
  deptId: number | null
  deptName: string
  onClose: () => void
}

export default function FnDeptMembers({ open, deptId, deptName, onClose }: Props) {
  const { data: members = [], isLoading, error } = useDeptMembersQuery(open ? deptId : null)

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ fontWeight: 800 }}>{deptName} — 成員列表</DialogTitle>
      <DialogContent sx={{ pt: '8px !important' }}>
        {error ? (
          <Alert severity="error">載入失敗：{(error as Error).message}</Alert>
        ) : isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
            <CircularProgress />
          </Box>
        ) : members.length === 0 ? (
          <Typography sx={{ fontSize: 14, color: '#64748b', py: 2, textAlign: 'center' }}>
            此部門目前沒有成員
          </Typography>
        ) : (
          <List disablePadding>
            {members.map((m, index) => (
              <Box key={m.id}>
                <ListItem disablePadding sx={{ py: 0.5 }}>
                  <ListItemText primary={m.name} primaryTypographyProps={{ fontSize: 14 }} />
                </ListItem>
                {index < members.length - 1 && <Divider />}
              </Box>
            ))}
          </List>
        )}
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          onClick={onClose}
          variant="outlined"
          sx={{ color: '#64748b', borderColor: '#cbd5e1' }}
        >
          關閉
        </Button>
      </DialogActions>
    </Dialog>
  )
}
