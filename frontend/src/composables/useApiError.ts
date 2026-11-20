import { ref } from 'vue';
import type { Ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { ApiError } from 'boot/api';

export function isNotFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

export function useDescribeError(): (error: unknown) => string {
  const { t } = useI18n();
  return (error) => (error instanceof ApiError ? error.detail : t('errorUnexpected'));
}

export interface ErrorState {
  errorMessage: Ref<string>;
  report: (error: unknown) => void;
}

/** Error state for a page: report() shows the backend's explanation. */
export function useErrorMessage(): ErrorState {
  const describe = useDescribeError();
  const errorMessage = ref('');

  function report(error: unknown): void {
    errorMessage.value = describe(error);
  }

  return { errorMessage, report };
}

/**
 * Error state for a page that works on a resource the learner owns. A 404
 * means the resource is not theirs (any more), so the page offers a restart
 * instead of the backend's "not found".
 */
export function useOwnedResourceError(): ErrorState & { notFound: Ref<boolean> } {
  const { t } = useI18n();
  const describe = useDescribeError();
  const errorMessage = ref('');
  const notFound = ref(false);

  function report(error: unknown): void {
    notFound.value = isNotFound(error);
    errorMessage.value = notFound.value ? t('errorNotYours') : describe(error);
  }

  return { errorMessage, notFound, report };
}
