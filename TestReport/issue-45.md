# TestReport：[SD] Workflow 完整流程驗證（TDD 改名後）

## 測試案例
| ID | 類型 | 前置條件 | 操作 | 預期結果 |  |  |
|----|------|---------|------|---------| --- | --- |
| T1 | 其他 | SA issue 已建立 | 確認 SA issue body 三段式格式 | 包含工作狀態、關聯Issue、關聯檔案三段 |  |  |
| T2 | 其他 | SA PR merge 完成 | 查看 P1-design 最新 issue | SD issue 自動建立，關聯檔案含 `TDD/issue-{N}.md` |  |  |
| T3 | 其他 | SD issue 已建立 | 確認 SD issue body 三段式格式 | 功能說明內嵌 business-logic.md，設計範圍內嵌 SD-WBS.md |  |  |
| T4 | 其他 | SD PR merge 完成 | 查看 P1-code 最新 issue | PG issue 自動建立，body 含 TDD 連結 |  |  |
| T5 | 其他 | SD PR merge 完成 | 查看 P1-code C-Branch | TestReport scaffold 自動產生，內容來源為 TDD/issue-{N}.md |  |  |

> 最低要求：每個 API 至少一個成功案例（2xx）+ 一個失敗案例（4xx/5xx）；每個畫面至少一個主流程案例
