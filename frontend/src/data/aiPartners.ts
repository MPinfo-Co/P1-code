export interface AiPartner {
  id: string
  name: string
  description: string
  builtin: boolean
  disabled: boolean
}

export const aiPartners: AiPartner[] = [
  {
    id: 'security-expert',
    name: '資安專家',
    description: '解析防火牆與系統日誌，自動偵測安全事件並提供優先級評估、處置建議與歷程追蹤。',
    builtin: true,
    disabled: false,
  },
  {
    id: 'order-secretary',
    name: '訂單智能秘書',
    description: '自動化處理電商訂單流程，分類退換貨請求與客服回覆。',
    builtin: false,
    disabled: true,
  },
]
