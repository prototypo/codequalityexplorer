// ESLint flat config for the quality-report skill: covers all six JS/TS
// extensions with the TypeScript parser, so one run lints every file exactly
// once. Shipped beside the skill because the skill never writes into the repo
// it analyses, and so the parser resolves from the skill's own node_modules.
import tseslint from 'typescript-eslint';
export default [{
  files: ['**/*.js', '**/*.jsx', '**/*.mjs', '**/*.cjs', '**/*.ts', '**/*.tsx'],
  languageOptions: { parser: tseslint.parser, parserOptions: { ecmaFeatures: { jsx: true } } },
}];
