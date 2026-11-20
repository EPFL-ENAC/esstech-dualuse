import enUS from './en-US';
import fr from './fr';

export type MessageKey = keyof typeof enUS;

export default {
  'en-US': enUS,
  fr: fr,
};
