module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
  ],
  ignorePatterns: ["dist", ".eslintrc.cjs"],
  parser: "@typescript-eslint/parser",
  plugins: ["react-refresh"],
  rules: {
    "react-refresh/only-export-components": [
      "warn",
      { allowConstantExport: true },
    ],
    "@typescript-eslint/no-explicit-any": "off",
  },
  overrides: [
    {
      // shadcn/ui 组件通常同时导出组件与样式变体函数，关闭 fast-refresh 限制
      files: ["src/components/ui/**/*.tsx"],
      rules: {
        "react-refresh/only-export-components": "off",
      },
    },
  ],
};
