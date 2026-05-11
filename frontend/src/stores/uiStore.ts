/**
 * uiStore — 全域 UI 狀態（通知、提示）
 * Zustand store，只管全域 UI 狀態，不存放 server data。
 */
import { create } from 'zustand'

interface UiState {
  /** 全域通知訊息，null 表示無訊息 */
  globalNotice: string | null
}

interface UiActions {
  setGlobalNotice: (msg: string | null) => void
  clearGlobalNotice: () => void
}

type UiStore = UiState & UiActions

const useUiStore = create<UiStore>((set) => ({
  globalNotice: null,

  setGlobalNotice: (msg) => set({ globalNotice: msg }),
  clearGlobalNotice: () => set({ globalNotice: null }),
}))

export default useUiStore
