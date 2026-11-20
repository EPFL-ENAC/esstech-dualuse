<template>
  <q-page class="landing-page">
    <section class="landing-hero">
      <div class="landing-hero__content">
        <div class="landing-hero__head">
          <div class="landing-hero__title-tab">
            <div class="landing-kicker">{{ t('landingKicker') }}</div>
            <h1 class="landing-title">
              {{ t('landingTitleLead') }} <span>{{ t('landingTitleAccent') }}</span>
            </h1>
          </div>
          <router-link class="landing-hero__cta" to="/start">
            <span>{{ t('landingTry') }}</span
            ><FeatherIcon name="arrow" />
          </router-link>
        </div>
        <div class="landing-hero__body">
          <p class="landing-lead">{{ t('landingLead') }}</p>
          <a class="landing-text-link" href="#how-it-works"
            >{{ t('landingDiscover') }} <FeatherIcon name="arrow"
          /></a>
          <div class="landing-meta">
            <div v-for="item in landingMeta" :key="item.label" class="landing-meta__item">
              <FeatherIcon :name="item.icon" /><span>{{ item.label }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="landing-visual" aria-hidden="true">
        <div class="landing-video-frame">
          <video
            class="landing-video"
            autoplay
            muted
            loop
            playsinline
            preload="metadata"
            poster="/media/dual-use-poster.webp"
          >
            <source src="/media/dual-use.mp4" type="video/mp4" />
          </video>
        </div>
      </div>
    </section>

    <section class="landing-paths">
      <div class="landing-paths__heading">
        <div>
          <h2>{{ t('landingPathsTitle') }}</h2>
        </div>
        <p>{{ t('landingPathsBody') }}</p>
      </div>

      <div class="landing-paths__grid">
        <router-link
          v-for="(path, index) in paths"
          :key="path.key"
          to="/start"
          class="landing-path-card"
        >
          <div class="landing-path-card__top">
            <div class="landing-path-card__icon"><FeatherIcon :name="path.icon" /></div>
            <span>0{{ index + 1 }}</span>
          </div>
          <div class="landing-path-card__content">
            <span>{{ t(`landing${path.key}Eyebrow`) }}</span>
            <h3>{{ t(`landing${path.key}Title`) }}</h3>
            <p>{{ t(`landing${path.key}Body`) }}</p>
            <div class="landing-path-card__features">
              <span>{{ t(`landing${path.key}FeatureOne`) }}</span>
              <span>{{ t(`landing${path.key}FeatureTwo`) }}</span>
            </div>
          </div>
          <div class="landing-path-card__action">
            {{ t('landingExploreRoute') }} <FeatherIcon name="arrow" />
          </div>
        </router-link>
      </div>
    </section>

    <section id="how-it-works" class="landing-section landing-section--band">
      <div class="landing-section__inner">
        <div class="landing-section__intro">
          <div>
            <h2>{{ t('landingHowTitle') }}</h2>
          </div>
          <p>{{ t('landingHowBody') }}</p>
        </div>
        <div class="landing-steps">
          <article v-for="step in steps" :key="step.title" class="landing-step">
            <div class="landing-step__top">
              <h3>{{ step.title }}</h3>
              <FeatherIcon :name="step.icon" />
            </div>
            <p>{{ step.body }}</p>
          </article>
        </div>
      </div>
    </section>
    <section class="landing-statement">
      <div class="landing-statement__mark">“</div>
      <div class="landing-statement__copy">
        <span>{{ t('landingStatementLabel') }}</span>
        <p>{{ t('landingStatement') }}</p>
      </div>
      <q-btn class="landing-secondary-action" color="primary" unelevated no-caps to="/start"
        ><span>{{ t('landingTryShort') }}</span
        ><FeatherIcon name="arrow"
      /></q-btn>
    </section>
  </q-page>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import FeatherIcon from 'components/FeatherIcon.vue';

defineOptions({ name: 'IndexPage' });
const { t } = useI18n();

const landingMeta = computed(() => [
  { icon: 'shield', label: t('landingMetaPrivacy') },
  { icon: 'thought', label: t('landingMetaNoScore') },
]);
const paths = [
  { key: 'Student', icon: 'student' },
  { key: 'Researcher', icon: 'research' },
];
const steps = computed(() => [
  { icon: 'explore', title: t('landingStepOneTitle'), body: t('landingStepOneBody') },
  { icon: 'branch', title: t('landingStepTwoTitle'), body: t('landingStepTwoBody') },
  { icon: 'eye', title: t('landingStepThreeTitle'), body: t('landingStepThreeBody') },
]);
</script>

<style scoped>
.landing-page {
  overflow: hidden;
  /* The picture runs under the glass header. */
  margin-top: calc(-1 * var(--header-h));
}

/* Hero: the signature EPFL layout. A white text panel overlaps the full-bleed
   picture and breaks its bottom edge. */
.landing-hero {
  display: grid;
  margin-bottom: var(--space-6);
}
.landing-visual {
  grid-area: 1 / 1;
}
.landing-video-frame {
  width: 100%;
  height: calc(clamp(22rem, 46vw, 34rem) + var(--header-h) + var(--space-5));
  background: var(--epfl-gray-200);
}
.landing-video {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.landing-hero__content {
  position: relative;
  z-index: 1;
  grid-area: 1 / 1;
  align-self: end;
  justify-self: start;
  width: min(46rem, calc(100% - 2 * var(--gutter)));
  margin: 0 0 var(--space-5) calc(var(--page-inset) + var(--gutter));
}
/* White title tab with a red action tab beside it, cut at an angle, over a
   translucent box: the "Visit EPFL" panel. */
.landing-hero__head {
  display: flex;
  align-items: flex-end;
}
.landing-hero__title-tab {
  padding: var(--space-4) var(--space-5) var(--space-3);
  background: var(--bg);
}
.landing-hero__cta {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  margin-left: -0.0625rem;
  padding: 0.75rem var(--space-4) 0.75rem var(--space-5);
  color: var(--fg-inverse);
  background: var(--primary);
  clip-path: polygon(1.25rem 0, 100% 0, 100% 100%, 0 100%);
  font-weight: var(--w-bold);
  text-decoration: none;
  white-space: nowrap;
  transition: background var(--t-base);
}
.landing-hero__cta:hover {
  color: var(--fg-inverse);
  background: var(--primary-hover);
}
.landing-hero__cta:focus-visible {
  outline: var(--focus-w) solid var(--fg);
  outline-offset: -0.25rem;
}
.landing-hero__cta .feather-icon {
  width: 1.25em;
  height: 1.25em;
}
.landing-hero__body {
  width: 72%;
  margin-left: auto;
  padding: var(--space-4) var(--space-5);
  background: color-mix(in srgb, var(--bg) 92%, transparent);
}
.landing-kicker {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
  color: var(--fg-muted);
  font-size: var(--fs-sm);
  font-weight: var(--w-bold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.landing-kicker::before {
  content: '';
  flex: 0 0 auto;
  width: var(--marker-w);
  height: var(--marker-h);
  background: var(--primary);
}
.landing-title {
  margin: 0;
  font-size: clamp(2rem, 4vw, var(--fs-h1));
  font-weight: var(--w-bold);
  line-height: var(--lh-tight);
}
.landing-title span {
  color: var(--primary);
}
.landing-lead {
  max-width: 34rem;
  margin: 0 0 var(--space-3);
  font-size: var(--fs-lead);
  line-height: var(--lh-relaxed);
}
.landing-secondary-action {
  padding: 0.68rem 1.4rem;
  font-size: var(--fs-body);
}
.landing-secondary-action :deep(.q-btn__content) {
  gap: var(--space-2);
}
.landing-text-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-weight: var(--w-bold);
}
.landing-text-link .feather-icon,
.landing-path-card__action .feather-icon {
  width: 1.25em;
  height: 1.25em;
}
.landing-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-4);
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: var(--border-w) solid var(--border-hairline);
  color: var(--fg-muted);
  font-size: var(--fs-sm);
}
.landing-meta__item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}
.landing-meta__item .feather-icon {
  width: 1.25em;
  height: 1.25em;
}

.landing-paths,
.landing-section {
  width: min(var(--content-w), 100%);
  margin: 0 auto var(--space-6);
  padding: 0 var(--gutter);
}
.landing-paths__heading,
.landing-section__intro {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-4) var(--space-5);
  align-items: end;
  margin-bottom: var(--space-5);
}
.landing-paths__heading h2,
.landing-section__intro h2 {
  margin: 0;
  font-size: var(--fs-h2);
  line-height: var(--lh-snug);
}
.landing-paths__heading p,
.landing-section__intro p {
  max-width: 34rem;
  margin: 0;
  color: var(--fg-muted);
  font-size: var(--fs-lead);
  line-height: var(--lh-relaxed);
}

.landing-paths__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--gutter);
}
.landing-path-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4);
  color: var(--fg);
  background: var(--bg);
  border: var(--border-w) solid var(--border);
  text-decoration: none;
  transition: border-color var(--t-base);
}
.landing-path-card:hover {
  color: var(--fg);
  border-color: var(--fg);
}
.landing-path-card:focus-visible {
  outline: var(--focus-w) solid var(--primary-hover);
  outline-offset: 0.125rem;
}
.landing-path-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--fg-muted);
  font-size: var(--fs-sm);
  font-weight: var(--w-bold);
}
.landing-path-card__icon {
  display: grid;
  place-items: center;
  width: 3.5rem;
  height: 3.5rem;
  color: var(--primary);
  background: var(--bg-subtle);
  border: var(--border-w) solid var(--border);
  border-radius: var(--radius);
}
.landing-path-card__content > span {
  display: block;
  margin-bottom: var(--space-2);
  color: var(--fg-muted);
  font-size: var(--fs-sm);
  font-weight: var(--w-bold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.landing-path-card__content h3 {
  margin: 0 0 var(--space-2);
  font-size: var(--fs-h4);
  font-weight: var(--w-bold);
  line-height: var(--lh-snug);
}
.landing-path-card__content p {
  margin: 0;
  line-height: var(--lh-relaxed);
}
.landing-path-card__features {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
}
.landing-path-card__features span {
  padding: 0.25rem 0.625rem;
  color: var(--fg);
  background: var(--bg);
  border: var(--border-w) solid var(--epfl-gray-300);
  border-radius: var(--radius);
  font-size: var(--fs-xs);
}
.landing-path-card__action {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: auto;
  color: var(--primary);
  font-weight: var(--w-bold);
}

/* How it works: the "Missions" band. A grey strip, white cards with the title
   and a large icon on top, a rule, then the text. */
.landing-section--band {
  width: 100%;
  padding: var(--space-5) 0;
  background: var(--epfl-gray-100);
}
.landing-section__inner {
  width: min(var(--content-w), 100%);
  margin: 0 auto;
  padding: 0 var(--gutter);
}
.landing-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--gutter);
}
.landing-step {
  display: flex;
  flex-direction: column;
  padding: var(--space-4);
  background: var(--bg);
  border: var(--border-w) solid var(--border);
}
.landing-step__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  min-height: 5.5rem;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: var(--border-w) solid var(--border-hairline);
}
.landing-step__top h3 {
  margin: 0;
  font-size: var(--fs-h4);
  font-weight: var(--w-normal);
  line-height: var(--lh-snug);
}
.landing-step__top .feather-icon {
  flex: 0 0 auto;
  width: 3.5rem;
  height: 3.5rem;
  color: var(--epfl-black);
  stroke-width: 1.5;
}
.landing-step p {
  margin: 0;
  line-height: var(--lh-relaxed);
}

/* Hover on a route card, as on epfl.ch: the border turns black and a flat grey
   strip slides out under the bottom edge. */
.landing-path-card {
  box-shadow: 0.75rem 1.25rem 0 -0.75rem transparent;
  transition:
    box-shadow 0.3s ease,
    border-color var(--t-base);
}
.landing-path-card:hover,
.landing-path-card:focus-visible {
  border-color: var(--fg);
  box-shadow: 0.75rem 1.25rem 0 -0.75rem var(--epfl-gray-300);
}

/* Closing statement, set like an EPFL pull quote. */
.landing-statement {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-4) var(--space-5);
  padding: var(--space-5) calc(var(--page-inset) + var(--gutter));
  background: var(--bg);
}
.landing-statement__mark {
  color: var(--primary);
  font-size: 5rem;
  font-style: italic;
  line-height: 0.6;
}
.landing-statement__copy span {
  display: block;
  margin-bottom: var(--space-2);
  color: var(--fg-muted);
  font-size: var(--fs-sm);
  font-weight: var(--w-bold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.landing-statement__copy p {
  max-width: 44rem;
  margin: 0;
  font-size: var(--fs-h4);
  font-style: italic;
  line-height: var(--lh-normal);
}

@media (max-width: 62rem) {
  .landing-hero__title-tab {
    padding: var(--space-3) var(--space-4);
  }
  .landing-steps {
    grid-template-columns: 1fr;
  }
  .landing-statement {
    grid-template-columns: 1fr;
    justify-items: start;
  }
}
@media (max-width: 48rem) {
  .landing-hero {
    display: flex;
    flex-direction: column-reverse;
    margin-bottom: var(--space-5);
  }
  .landing-video-frame {
    height: calc(14rem + var(--header-h));
  }
  .landing-hero__content {
    width: auto;
    margin: calc(-1 * var(--space-4)) var(--space-3) 0;
  }
  .landing-hero__head {
    flex-wrap: wrap;
  }
  .landing-hero__body {
    width: auto;
    padding: var(--space-3) var(--space-4);
  }
  .landing-section__inner {
    padding: 0 var(--space-3);
  }
  .landing-section--band {
    padding: var(--space-5) 0;
  }
  .landing-paths,
  .landing-section {
    margin-bottom: var(--space-5);
    padding: 0 var(--space-3);
  }
  .landing-paths__heading,
  .landing-section__intro,
  .landing-paths__grid {
    grid-template-columns: 1fr;
  }
  .landing-statement {
    padding: var(--space-5) var(--space-3);
  }
}
</style>
