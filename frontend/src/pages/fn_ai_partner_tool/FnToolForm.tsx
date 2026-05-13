// src/pages/fn_ai_partner_tool/FnToolForm.tsx
import { useState } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import Radio from '@mui/material/Radio'
import RadioGroup from '@mui/material/RadioGroup'
import FormControlLabel from '@mui/material/FormControlLabel'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import Checkbox from '@mui/material/Checkbox'
import IconButton from '@mui/material/IconButton'
import Divider from '@mui/material/Divider'
import { useCreateTool, useUpdateTool, useTestTool } from '@/queries/useToolsQuery'
import type {
  ToolRow,
  BodyParam,
  ImageField,
  ToolType,
  TestToolResult,
} from '@/queries/useToolsQuery'
import './FnToolForm.css'

interface Props {
  open: boolean
  row: ToolRow | null
  onClose: () => void
  onSuccess: () => void
}

type AuthType = 'none' | 'api_key' | 'bearer'
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'
type ParamType = 'string' | 'number' | 'boolean' | 'object'
type ImageFieldType = 'string' | 'number'

export default function FnToolForm({ open, row, onClose, onSuccess }: Props) {
  const isEdit = !!row

  const [name, setName] = useState(() => row?.name ?? '')
  const [description, setDescription] = useState(() => row?.description ?? '')
  const [toolType, setToolType] = useState<ToolType>(() => row?.tool_type ?? 'external_api')
  const [endpointUrl, setEndpointUrl] = useState(() => row?.endpoint_url ?? '')
  const [authType, setAuthType] = useState<AuthType>(() => row?.auth_type ?? 'none')
  const [authHeaderName, setAuthHeaderName] = useState(() => row?.auth_header_name ?? '')
  const [credential, setCredential] = useState('')
  const [httpMethod, setHttpMethod] = useState<HttpMethod>(() => row?.http_method ?? 'GET')
  const [bodyParams, setBodyParams] = useState<BodyParam[]>(() => row?.body_params ?? [])
  const [imageFields, setImageFields] = useState<ImageField[]>(() => row?.image_fields ?? [])
  const [formError, setFormError] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<TestToolResult | null>(null)
  const [testError, setTestError] = useState<string | null>(null)
  const [testParamValues, setTestParamValues] = useState<Record<string, string>>(() => {
    const init: Record<string, string> = {}
    for (const p of row?.body_params ?? []) init[p.param_name] = ''
    return init
  })

  const createTool = useCreateTool()
  const updateTool = useUpdateTool()
  const testTool = useTestTool()

  const isPending = createTool.isPending || updateTool.isPending
  const isExternalApi = toolType === 'external_api'
  const isImageExtract = toolType === 'image_extract'
  const showBodyParams = isExternalApi && (httpMethod === 'POST' || httpMethod === 'PUT')
  const showHeaderName = authType === 'api_key'
  const showCredential = authType === 'api_key' || authType === 'bearer'

  function handleAddBodyParam() {
    setBodyParams((prev) => [
      ...prev,
      { param_name: '', param_type: 'string', is_required: false, description: '' },
    ])
  }

  function handleRemoveBodyParam(index: number) {
    setBodyParams((prev) => prev.filter((_, i) => i !== index))
  }

  function handleBodyParamChange(index: number, field: keyof BodyParam, value: unknown) {
    setBodyParams((prev) => prev.map((p, i) => (i === index ? { ...p, [field]: value } : p)))
  }

  function handleAddImageField() {
    setImageFields((prev) => [...prev, { field_name: '', field_type: 'string', description: '' }])
  }

  function handleRemoveImageField(index: number) {
    setImageFields((prev) => prev.filter((_, i) => i !== index))
  }

  function handleImageFieldChange(index: number, field: keyof ImageField, value: unknown) {
    setImageFields((prev) => prev.map((f, i) => (i === index ? { ...f, [field]: value } : f)))
  }

  async function handleTest() {
    setTestResult(null)
    setTestError(null)
    if (!endpointUrl.trim()) {
      setTestError('請先填寫 API Endpoint URL')
      return
    }
    try {
      const bodyParamsValues =
        showBodyParams && bodyParams.length > 0
          ? Object.fromEntries(
              bodyParams.map((p) => [p.param_name, testParamValues[p.param_name] ?? ''])
            )
          : undefined
      const result = await testTool.mutateAsync({
        endpoint_url: endpointUrl.trim(),
        auth_type: authType,
        auth_header_name: authType === 'api_key' ? authHeaderName.trim() || null : null,
        credential: credential.trim() || undefined,
        http_method: httpMethod,
        tool_id: isEdit && row ? row.id : undefined,
        body_params_values: bodyParamsValues,
      })
      setTestResult(result)
    } catch (err) {
      setTestError(err instanceof Error ? err.message : '測試失敗')
    }
  }

  async function handleSave() {
    setFormError(null)
    if (!name.trim()) {
      setFormError('請填寫工具名稱')
      return
    }

    if (isExternalApi && !endpointUrl.trim()) {
      setFormError('請填寫 API Endpoint URL')
      return
    }

    if (isImageExtract) {
      if (imageFields.length === 0) {
        setFormError('圖片擷取工具至少需設定一個擷取欄位')
        return
      }
      const hasEmptyFieldName = imageFields.some((f) => !f.field_name.trim())
      if (hasEmptyFieldName) {
        setFormError('請填寫欄位名稱')
        return
      }
    }

    try {
      if (isEdit && row) {
        const payload = isExternalApi
          ? {
              name: name.trim(),
              description: description.trim(),
              endpoint_url: endpointUrl.trim(),
              auth_type: authType,
              auth_header_name: authType === 'api_key' ? authHeaderName.trim() || null : null,
              credential: credential.trim() || undefined,
              http_method: httpMethod,
              body_params: showBodyParams ? bodyParams.filter((p) => p.param_name.trim()) : [],
            }
          : {
              name: name.trim(),
              description: description.trim(),
              image_fields: imageFields,
            }
        await updateTool.mutateAsync({ id: row.id, payload })
      } else {
        const payload = isExternalApi
          ? {
              name: name.trim(),
              description: description.trim(),
              tool_type: toolType,
              endpoint_url: endpointUrl.trim(),
              auth_type: authType,
              auth_header_name: authType === 'api_key' ? authHeaderName.trim() || null : null,
              credential: credential.trim() || undefined,
              http_method: httpMethod,
              body_params: showBodyParams ? bodyParams.filter((p) => p.param_name.trim()) : [],
            }
          : {
              name: name.trim(),
              description: description.trim(),
              tool_type: toolType,
              image_fields: imageFields,
            }
        await createTool.mutateAsync(payload)
      }
      onSuccess()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '操作失敗，請稍後再試')
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle className="fn-tool-form-title">{isEdit ? '編輯工具' : '新增工具'}</DialogTitle>
      <DialogContent sx={{ pt: '16px !important' }}>
        <Box className="fn-tool-form-stack">
          {formError && (
            <Alert severity="error" onClose={() => setFormError(null)}>
              {formError}
            </Alert>
          )}

          {/* 描述資訊 */}
          <Typography className="fn-tool-form-section-title">描述資訊</Typography>

          <Box>
            <Typography className="fn-tool-form-label">
              工具名稱 <span style={{ color: '#ef4444' }}>*</span>
            </Typography>
            <TextField
              fullWidth
              size="small"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="請輸入工具名稱"
              inputProps={{ maxLength: 100 }}
              sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
            />
          </Box>

          <Box>
            <Typography className="fn-tool-form-label">工具說明</Typography>
            <TextField
              fullWidth
              size="small"
              multiline
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="描述此工具能做什麼、適合在什麼情境使用（供 AI 夥伴識別用）"
              sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
            />
          </Box>

          <Box>
            <Typography className="fn-tool-form-label">
              工具類型 <span style={{ color: '#ef4444' }}>*</span>
            </Typography>
            {isEdit ? (
              <Typography sx={{ fontSize: 14, color: '#334155', py: 0.5 }}>
                {toolType === 'image_extract' ? '圖片擷取' : '外部 API 呼叫'}
              </Typography>
            ) : (
              <RadioGroup
                row
                value={toolType}
                onChange={(e) => setToolType(e.target.value as ToolType)}
              >
                <FormControlLabel
                  value="external_api"
                  control={<Radio size="small" />}
                  label="外部 API 呼叫"
                />
                <FormControlLabel
                  value="image_extract"
                  control={<Radio size="small" />}
                  label="圖片擷取"
                />
              </RadioGroup>
            )}
          </Box>

          <Divider />

          {/* 連線資訊（工具類型為「外部 API 呼叫」時顯示） */}
          {isExternalApi && (
            <Typography className="fn-tool-form-section-title">連線資訊</Typography>
          )}

          {/* 連線資訊區段（僅「外部 API 呼叫」顯示） */}
          {isExternalApi && (
            <>
              <Box>
                <Typography className="fn-tool-form-label">
                  API Endpoint URL <span style={{ color: '#ef4444' }}>*</span>
                </Typography>
                <TextField
                  fullWidth
                  size="small"
                  value={endpointUrl}
                  onChange={(e) => setEndpointUrl(e.target.value)}
                  placeholder="https://api.example.com/v1/action 或 /resource/{id}"
                  sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
                />
                <Typography sx={{ fontSize: 12, color: '#64748b', mt: 0.5 }}>
                  路徑與 query 中的 &#123;xxx&#125; 會在呼叫時由 AI 夥伴動態帶入
                </Typography>
              </Box>

              <Box>
                <Typography className="fn-tool-form-label">認證方式</Typography>
                <RadioGroup
                  row
                  value={authType}
                  onChange={(e) => setAuthType(e.target.value as AuthType)}
                >
                  <FormControlLabel value="none" control={<Radio size="small" />} label="無認證" />
                  <FormControlLabel
                    value="api_key"
                    control={<Radio size="small" />}
                    label="API Key"
                  />
                  <FormControlLabel
                    value="bearer"
                    control={<Radio size="small" />}
                    label="Bearer Token"
                  />
                </RadioGroup>
              </Box>

              {showHeaderName && (
                <Box>
                  <Typography className="fn-tool-form-label">
                    Header 名稱 <span style={{ color: '#ef4444' }}>*</span>
                  </Typography>
                  <TextField
                    fullWidth
                    size="small"
                    value={authHeaderName}
                    onChange={(e) => setAuthHeaderName(e.target.value)}
                    placeholder="X-API-Key"
                    sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
                  />
                </Box>
              )}

              {showCredential && (
                <Box>
                  <Typography className="fn-tool-form-label">
                    {authType === 'api_key' ? 'API Key 憑證' : 'Bearer Token 憑證'}
                    {!isEdit && <span style={{ color: '#ef4444' }}> *</span>}
                  </Typography>
                  <TextField
                    fullWidth
                    size="small"
                    type="password"
                    value={credential}
                    onChange={(e) => setCredential(e.target.value)}
                    placeholder={isEdit ? '' : '請輸入憑證'}
                    sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
                  />
                  {isEdit && row?.has_credential && (
                    <Typography sx={{ fontSize: 12, color: '#64748b', mt: 0.5 }}>
                      已設定，如需變更請重新輸入，保持空白即不變更
                    </Typography>
                  )}
                </Box>
              )}

              <Box>
                <Typography className="fn-tool-form-label">HTTP Method</Typography>
                <RadioGroup
                  row
                  value={httpMethod}
                  onChange={(e) => setHttpMethod(e.target.value as HttpMethod)}
                >
                  {(['GET', 'POST', 'PUT', 'DELETE'] as HttpMethod[]).map((m) => (
                    <FormControlLabel
                      key={m}
                      value={m}
                      control={<Radio size="small" />}
                      label={m}
                    />
                  ))}
                </RadioGroup>
              </Box>

              {/* Body 參數定義（僅 POST / PUT 時顯示） */}
              {showBodyParams && (
                <Box>
                  <Typography className="fn-tool-form-section-title">Body 參數定義</Typography>
                  {bodyParams.map((param, index) => (
                    <Box key={index} className="fn-tool-param-row">
                      <TextField
                        size="small"
                        placeholder="參數名稱"
                        value={param.param_name}
                        onChange={(e) => handleBodyParamChange(index, 'param_name', e.target.value)}
                        sx={{ flex: 1, minWidth: 100, '& .MuiInputBase-input': { fontSize: 13 } }}
                      />
                      <Select
                        size="small"
                        value={param.param_type}
                        onChange={(e) =>
                          handleBodyParamChange(index, 'param_type', e.target.value as ParamType)
                        }
                        sx={{ minWidth: 100, fontSize: 13 }}
                      >
                        {(['string', 'number', 'boolean', 'object'] as ParamType[]).map((t) => (
                          <MenuItem key={t} value={t} sx={{ fontSize: 13 }}>
                            {t}
                          </MenuItem>
                        ))}
                      </Select>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Checkbox
                          size="small"
                          checked={param.is_required}
                          onChange={(e) =>
                            handleBodyParamChange(index, 'is_required', e.target.checked)
                          }
                        />
                        <Typography sx={{ fontSize: 13, color: '#475569', whiteSpace: 'nowrap' }}>
                          必填
                        </Typography>
                      </Box>
                      <TextField
                        size="small"
                        placeholder="說明此參數的用途與範例值"
                        value={param.description}
                        onChange={(e) =>
                          handleBodyParamChange(index, 'description', e.target.value)
                        }
                        sx={{ flex: 2, '& .MuiInputBase-input': { fontSize: 13 } }}
                      />
                      <IconButton
                        size="small"
                        onClick={() => handleRemoveBodyParam(index)}
                        aria-label="刪除參數"
                      >
                        ×
                      </IconButton>
                    </Box>
                  ))}
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={handleAddBodyParam}
                    sx={{ mt: 1, fontSize: 12 }}
                  >
                    ＋ 新增參數
                  </Button>
                </Box>
              )}

              <Divider />

              {/* 測試區塊（僅外部 API 呼叫顯示） */}
              <Typography className="fn-tool-form-section-title">測試</Typography>

              {showBodyParams && bodyParams.filter((p) => p.param_name.trim()).length > 0 && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Typography sx={{ fontSize: 13, color: '#475569' }}>測試參數值</Typography>
                  {bodyParams
                    .filter((p) => p.param_name.trim())
                    .map((param) => (
                      <Box
                        key={param.param_name}
                        sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
                      >
                        <Typography sx={{ fontSize: 13, minWidth: 120, color: '#334155' }}>
                          {param.param_name}
                          {param.is_required && <span style={{ color: '#ef4444' }}> *</span>}
                        </Typography>
                        <TextField
                          size="small"
                          fullWidth
                          placeholder={`${param.param_type}${param.description ? `（${param.description}）` : ''}`}
                          value={testParamValues[param.param_name] ?? ''}
                          onChange={(e) =>
                            setTestParamValues((prev) => ({
                              ...prev,
                              [param.param_name]: e.target.value,
                            }))
                          }
                          sx={{ '& .MuiInputBase-input': { fontSize: 13 } }}
                        />
                      </Box>
                    ))}
                </Box>
              )}

              <Box>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleTest}
                  disabled={testTool.isPending}
                  sx={{ fontSize: 13 }}
                >
                  {testTool.isPending ? <CircularProgress size={16} /> : '測試'}
                </Button>
              </Box>

              {testError && (
                <Alert severity="error" onClose={() => setTestError(null)}>
                  {testError}
                </Alert>
              )}

              {testResult && (
                <Box
                  sx={{
                    background: testResult.http_status < 400 ? '#f0fdf4' : '#fef2f2',
                    border: `1px solid ${testResult.http_status < 400 ? '#86efac' : '#fca5a5'}`,
                    color: testResult.http_status < 400 ? '#166534' : '#991b1b',
                    borderRadius: 1,
                    p: 1.5,
                    fontSize: 13,
                  }}
                >
                  <Typography sx={{ fontWeight: 600, mb: 1, fontSize: 13 }}>
                    {testResult.http_status < 400
                      ? `✓ 呼叫成功（${testResult.http_status} OK）`
                      : `✗ 呼叫結果（${testResult.http_status}）`}
                  </Typography>
                  <Box
                    component="pre"
                    sx={{
                      m: 0,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-all',
                      fontSize: 12,
                      background: 'rgba(0,0,0,0.04)',
                      p: 1,
                      borderRadius: 0.5,
                      maxHeight: 160,
                      overflowY: 'auto',
                    }}
                  >
                    {JSON.stringify(testResult.response_body, null, 2)}
                  </Box>
                </Box>
              )}
            </>
          )}

          {/* 擷取欄位定義區段（僅「圖片擷取」顯示） */}
          {isImageExtract && (
            <>
              <Typography className="fn-tool-form-section-title">擷取欄位定義</Typography>
              <Typography sx={{ fontSize: 13, color: '#64748b', mb: 1 }}>
                定義 AI 夥伴從圖片中擷取的欄位，至少需設定一個欄位。
              </Typography>
              {imageFields.map((field, index) => (
                <Box key={index} className="fn-tool-param-row">
                  <TextField
                    size="small"
                    placeholder="欄位名稱"
                    value={field.field_name}
                    onChange={(e) => handleImageFieldChange(index, 'field_name', e.target.value)}
                    sx={{ flex: 1, minWidth: 120, '& .MuiInputBase-input': { fontSize: 13 } }}
                  />
                  <Select
                    size="small"
                    value={field.field_type}
                    onChange={(e) =>
                      handleImageFieldChange(index, 'field_type', e.target.value as ImageFieldType)
                    }
                    sx={{ minWidth: 100, fontSize: 13 }}
                  >
                    {(['string', 'number'] as ImageFieldType[]).map((t) => (
                      <MenuItem key={t} value={t} sx={{ fontSize: 13 }}>
                        {t}
                      </MenuItem>
                    ))}
                  </Select>
                  <TextField
                    size="small"
                    placeholder="說明此欄位代表的資訊"
                    value={field.description}
                    onChange={(e) => handleImageFieldChange(index, 'description', e.target.value)}
                    sx={{ flex: 2, '& .MuiInputBase-input': { fontSize: 13 } }}
                  />
                  <IconButton
                    size="small"
                    onClick={() => handleRemoveImageField(index)}
                    aria-label="刪除欄位"
                  >
                    ×
                  </IconButton>
                </Box>
              ))}
              <Button
                variant="outlined"
                size="small"
                onClick={handleAddImageField}
                sx={{ mt: 1, fontSize: 12 }}
              >
                ＋ 新增欄位
              </Button>
            </>
          )}
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} className="fn-tool-form-cancel-btn" disabled={isPending}>
          取消
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={isPending}
          className="fn-tool-form-save-btn"
        >
          {isPending ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
