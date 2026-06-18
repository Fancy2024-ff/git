import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

// NOTE: must be vite.config.ts (NOT .mjs). @dcloudio/vite-plugin-uni ships as
// CommonJS; under native ESM (.mjs without "type":"module") the default import
// resolves to the module namespace object instead of the callable factory,
// producing "uni is not a function" at build time. esbuild's CJS->ESM interop
// in the .ts path makes `uni` callable. See QA build check.
export default defineConfig({
  plugins: [uni()],
})
