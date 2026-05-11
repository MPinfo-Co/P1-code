import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'
import prettier from 'eslint-config-prettier'
import tsPlugin from '@typescript-eslint/eslint-plugin'
import tsParser from '@typescript-eslint/parser'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
      prettier,
    ],
    plugins: { '@typescript-eslint': tsPlugin },
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
      // TypeScript 編譯器已涵蓋型別檢查（含 DOM lib 類型如 RequestInfo/RequestInit），
      // no-undef 在 TS 檔中為多餘且易誤報，統一關閉。
      'no-undef': 'off',
      // React 19 嚴格 rule, 但本地與 CI 的 plugin 版本判斷不一致 (本地不擋, CI 擋),
      // 改 warn 避免 inline disable 被 lint-staged eslint --fix 移除導致 CI 失敗。
      // 重構成 react-query / key prop 後再改回 error: 另開 chore issue 處理。
      'react-hooks/set-state-in-effect': 'warn',
    },
  },
])
