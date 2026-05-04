import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import type { KnowledgeBase } from '@/data/knowledgeBase'
import './AccessTab.css'

interface Props {
  kb: KnowledgeBase
}

export default function AccessTab({ kb }: Props) {
  return (
    <Box>
      <Typography className="access-tab-title">存取設定</Typography>
      <Typography className="access-tab-subtitle">以下角色可存取此知識庫：</Typography>
      <Box className="access-tab-list">
        {kb.accessRoles.map((role) => (
          <Box key={role} className="access-tab-row">
            <Typography className="access-tab-role">{role}</Typography>
            <Button size="small" className="access-tab-remove">
              移除
            </Button>
          </Box>
        ))}
      </Box>
      <Button variant="outlined" size="small" className="access-tab-add">
        + 新增角色存取
      </Button>
    </Box>
  )
}
