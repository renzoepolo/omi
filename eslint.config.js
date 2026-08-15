import js from '@eslint/js';
import globals from 'globals';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import prettier from 'eslint-config-prettier';

export default [
  {
    ignores: [
      'dist/**',
      'node_modules/**',
      '.venv/**',
      'coverage/**',
      'docs/architecture/generated/**',
    ],
  },
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.browser },
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    settings: {
      react: { version: 'detect' },
    },
    plugins: {
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    // Las reglas se declaran una por una a proposito: eslint-plugin-react-hooks
    // esta en 5.1.0-rc y sus configs preempaquetadas para flat config cambian
    // entre release candidates.
    rules: {
      // Sin estas dos reglas, no-unused-vars no ve los identificadores usados
      // dentro de JSX y marca como muerto todo componente importado.
      'react/jsx-uses-vars': 'error',
      'react/jsx-uses-react': 'error',
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    },
  },
  {
    // Archivos de configuracion y scripts que corren en Node, no en el browser.
    files: ['*.config.js', 'scripts/**/*.js'],
    languageOptions: {
      globals: { ...globals.node },
    },
  },
  prettier,
];
