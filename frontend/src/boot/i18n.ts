import { defineBoot } from '#q-app/wrappers';
import { computed } from 'vue';
import { createI18n } from 'vue-i18n';

import messages from 'src/i18n';

export type MessageLanguages = keyof typeof messages;
export type MessageSchema = (typeof messages)['en-US'];

// See https://vue-i18n.intlify.dev/guide/advanced/typescript.html#global-resource-schema-type-definition
/* eslint-disable @typescript-eslint/no-empty-object-type */
declare module 'vue-i18n' {
  export interface DefineLocaleMessage extends MessageSchema {}

  export interface DefineDateTimeFormat {}

  export interface DefineNumberFormat {}
}
/* eslint-enable @typescript-eslint/no-empty-object-type */

export const LOCALES = Object.keys(messages) as MessageLanguages[];

/** Each locale's name in its own language, for the switcher. */
export const LOCALE_NAMES = {
  'en-US': 'English',
  fr: 'Français',
} as const satisfies Record<MessageLanguages, string>;

const STORAGE_KEY = 'app-locale';

function isLocale(value: string | null): value is MessageLanguages {
  return LOCALES.some((locale) => locale === value);
}

function getInitialLocale(): MessageLanguages {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (isLocale(stored)) {
    return stored;
  }

  if (navigator.language.toLowerCase().startsWith('fr')) {
    return 'fr';
  }

  return 'en-US';
}

const i18n = createI18n<{ message: MessageSchema }, MessageLanguages, false>({
  locale: getInitialLocale(),
  legacy: false,
  messages,
});

/** Switch the UI language and remember the choice for the next visit. */
export function setLocale(locale: MessageLanguages): void {
  i18n.global.locale.value = locale;
  localStorage.setItem(STORAGE_KEY, locale);
}

/** The locale the switcher offers next, cycling through LOCALES. */
export const nextLocale = computed<MessageLanguages>(() => {
  const current = i18n.global.locale.value;
  return LOCALES[(LOCALES.indexOf(current) + 1) % LOCALES.length] ?? current;
});

export default defineBoot(({ app }) => {
  app.use(i18n);
});
