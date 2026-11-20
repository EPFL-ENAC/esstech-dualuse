import { defineConfig } from '#q-app/wrappers';
import { fileURLToPath } from 'node:url';

export default defineConfig(() => {
  return {
    boot: ['i18n'],

    css: ['epfl/tokens/colors_and_type.css', 'app.scss'],

    extras: ['material-icons', 'material-symbols-rounded'],

    build: {
      target: {
        browser: ['es2022', 'firefox115', 'chrome115', 'safari14'],
        node: 'node20',
      },

      typescript: {
        strict: true,
        vueShim: true,
      },

      vueRouterMode: 'history',

      vitePlugins: [
        [
          '@intlify/unplugin-vue-i18n/vite',
          {
            include: [fileURLToPath(new URL('./src/i18n', import.meta.url))],
          },
        ],

        [
          'vite-plugin-checker',
          {
            vueTsc: true,
            eslint: {
              lintCommand: 'eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"',
              useFlatConfig: true,
            },
          },
          { server: false },
        ],
      ],
    },

    devServer: {
      port: 9000, // matches backend CORS default
      open: true,
    },

    framework: {
      config: {},
    },

    animations: [],
  };
});
