<template>
  <q-page class="landing-page">
    <section class="landing-hero">
      <div class="landing-hero__content">
        <div class="landing-kicker">{{ t('landingKicker') }}</div>
        <h1 class="landing-title">
          {{ t('landingTitleLead') }} <span>{{ t('landingTitleAccent') }}</span>
        </h1>
        <p class="landing-lead">{{ t('landingLead') }}</p>
        <div class="landing-actions">
          <q-btn class="landing-primary-action" unelevated no-caps to="/start">
            <span>{{ t('landingTry') }}</span
            ><HandDrawnIcon name="arrow" />
          </q-btn>
          <a class="landing-text-link" href="#how-it-works"
            >{{ t('landingDiscover') }} <HandDrawnIcon name="arrow"
          /></a>
        </div>
        <div class="landing-meta">
          <div v-for="item in landingMeta" :key="item.label" class="landing-meta__item">
            <HandDrawnIcon :name="item.icon" /><span>{{ item.label }}</span>
          </div>
        </div>
      </div>
      <div class="landing-visual" aria-hidden="true">
        <div class="landing-video-frame" :style="videoFrameStyle">
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
        <router-link to="/start" class="landing-path-card landing-path-card--student">
          <div class="landing-path-card__top">
            <div class="landing-path-card__icon"><HandDrawnIcon name="student" /></div>
            <span>01</span>
          </div>
          <div class="landing-path-card__content">
            <span>{{ t('landingStudentEyebrow') }}</span>
            <h3>{{ t('landingStudentTitle') }}</h3>
            <p>{{ t('landingStudentBody') }}</p>
            <div class="landing-path-card__features">
              <span>{{ t('landingStudentFeatureOne') }}</span>
              <span>{{ t('landingStudentFeatureTwo') }}</span>
            </div>
          </div>
          <div class="landing-path-card__action">
            {{ t('landingExploreRoute') }} <HandDrawnIcon name="arrow" />
          </div>
        </router-link>

        <router-link to="/start" class="landing-path-card landing-path-card--researcher">
          <div class="landing-path-card__top">
            <div class="landing-path-card__icon"><HandDrawnIcon name="research" /></div>
            <span>02</span>
          </div>
          <div class="landing-path-card__content">
            <span>{{ t('landingResearcherEyebrow') }}</span>
            <h3>{{ t('landingResearcherTitle') }}</h3>
            <p>{{ t('landingResearcherBody') }}</p>
            <div class="landing-path-card__features">
              <span>{{ t('landingResearcherFeatureOne') }}</span>
              <span>{{ t('landingResearcherFeatureTwo') }}</span>
            </div>
          </div>
          <div class="landing-path-card__action">
            {{ t('landingExploreRoute') }} <HandDrawnIcon name="arrow" />
          </div>
        </router-link>
      </div>
    </section>

    <section id="how-it-works" class="landing-section">
      <div class="landing-section__intro">
        <div>
          <h2>{{ t('landingHowTitle') }}</h2>
        </div>
        <p>{{ t('landingHowBody') }}</p>
      </div>
      <div class="landing-steps">
        <article v-for="(step, index) in steps" :key="step.title" class="landing-step">
          <div class="landing-step__top">
            <span>0{{ index + 1 }}</span
            ><HandDrawnIcon :name="step.icon" />
          </div>
          <h3>{{ step.title }}</h3>
          <p>{{ step.body }}</p>
        </article>
      </div>
    </section>
    <section class="landing-statement">
      <div class="landing-statement__mark">“</div>
      <div class="landing-statement__copy">
        <span>{{ t('landingStatementLabel') }}</span>
        <p>{{ t('landingStatement') }}</p>
      </div>
      <q-btn class="landing-secondary-action" unelevated no-caps to="/start"
        ><span>{{ t('landingTryShort') }}</span
        ><HandDrawnIcon name="arrow"
      /></q-btn>
    </section>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import HandDrawnIcon from 'components/HandDrawnIcon.vue';

defineOptions({ name: 'IndexPage' });
const { t } = useI18n();
const videoProgress = ref(0);
const compactViewport = ref(false);
let scrollFrame = 0;

const videoFrameStyle = computed(() => {
  const progress = videoProgress.value;
  const startWidth = compactViewport.value ? 88 : 72;
  return { width: `calc(${startWidth + progress * (100 - startWidth)}vw - ${progress * 48}px)` };
});

function updateVideoProgress(): void {
  scrollFrame = 0;
  compactViewport.value = window.innerWidth <= 600;
  const scrollRange = Math.min(620, window.innerHeight * 0.72);
  videoProgress.value = Math.min(1, Math.max(0, window.scrollY / scrollRange));
}

function handleScroll(): void {
  if (scrollFrame === 0) scrollFrame = window.requestAnimationFrame(updateVideoProgress);
}

onMounted(() => {
  updateVideoProgress();
  window.addEventListener('scroll', handleScroll, { passive: true });
  window.addEventListener('resize', handleScroll, { passive: true });
});

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll);
  window.removeEventListener('resize', handleScroll);
  if (scrollFrame !== 0) window.cancelAnimationFrame(scrollFrame);
});
const landingMeta = computed(() => [
  { icon: 'clock', label: t('landingMetaTime') },
  { icon: 'shield', label: t('landingMetaPrivacy') },
  { icon: 'thought', label: t('landingMetaNoScore') },
]);
const steps = computed(() => [
  { icon: 'explore', title: t('landingStepOneTitle'), body: t('landingStepOneBody') },
  { icon: 'branch', title: t('landingStepTwoTitle'), body: t('landingStepTwoBody') },
  { icon: 'idea', title: t('landingStepThreeTitle'), body: t('landingStepThreeBody') },
]);
</script>

<style scoped>
.landing-page {
  overflow: hidden;
}
.landing-hero {
  min-height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: clamp(60px, 8vw, 112px);
  width: 100%;
  margin: 0 auto;
  padding: clamp(96px, 12vw, 154px) 0 112px;
}
.landing-hero__content {
  position: relative;
  z-index: 2;
  width: min(1120px, calc(100% - 48px));
  text-align: center;
}
.landing-kicker {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--du-ink);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}
.landing-title {
  max-width: 1050px;
  margin: 32px auto 28px;
  color: #080b0b;
  font-family: var(--du-display);
  font-size: clamp(58px, 7.4vw, 108px);
  font-weight: 700;
  letter-spacing: -0.06em;
  line-height: 0.94;
}
.landing-title span {
  position: relative;
  display: inline-block;
  color: #080b0b;
  font-style: normal;
}
.landing-title span::after {
  content: '';
  position: absolute;
  right: 0;
  bottom: -0.06em;
  left: 0;
  height: 0.11em;
  background: #080b0b;
  border-radius: 50% 42% 55% 45%;
  transform: rotate(-1deg);
}
.landing-lead {
  max-width: 720px;
  margin: 0 auto;
  color: #202726;
  font-size: clamp(18px, 1.6vw, 22px);
  line-height: 1.55;
}
.landing-actions {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 28px;
  margin-top: 42px;
}
.landing-primary-action {
  min-height: 58px;
  padding: 0 24px;
  border: 2px solid var(--du-ink);
  border-radius: 16px 20px 14px 18px;
  background: var(--du-ink) !important;
  color: white !important;
  font-size: 16px;
  font-weight: 800;
  box-shadow: 6px 6px 0 var(--du-coral);
  transform: rotate(-0.7deg);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}
.landing-primary-action:hover {
  box-shadow: 3px 3px 0 var(--du-coral);
  transform: translate(3px, 3px) rotate(0);
}
.landing-primary-action :deep(.q-btn__content),
.landing-secondary-action :deep(.q-btn__content) {
  gap: 10px;
}
.landing-primary-action :deep(.hand-icon),
.landing-secondary-action :deep(.hand-icon) {
  width: 24px;
  height: 24px;
  transition: transform 0.18s ease;
}
.landing-primary-action:hover :deep(.hand-icon),
.landing-secondary-action:hover :deep(.hand-icon) {
  transform: translateX(4px) rotate(3deg);
}
.landing-text-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 2px 3px 7px;
  color: var(--du-ink);
  font-weight: 750;
  text-decoration: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 8' preserveAspectRatio='none'%3E%3Cpath d='M2 5.5C32 2 72 7 118 3' fill='none' stroke='%2312201f' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E");
  background-position: left bottom;
  background-size: 100% 7px;
  background-repeat: no-repeat;
}
.landing-text-link :deep(.hand-icon) {
  width: 23px;
  height: 23px;
  transition: transform 0.18s ease;
}
.landing-text-link:hover :deep(.hand-icon) {
  transform: translateX(4px) rotate(4deg);
}
.landing-meta {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 16px 26px;
  margin-top: 48px;
}
.landing-meta__item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--du-ink-soft);
  font-size: 13px;
}
.landing-meta__item :deep(.hand-icon) {
  width: 22px;
  height: 22px;
  color: var(--du-ink);
}
.landing-meta__item:nth-child(2) :deep(.hand-icon) {
  transform: rotate(3deg);
}
.landing-meta__item:nth-child(3) :deep(.hand-icon) {
  transform: rotate(-4deg);
}
.landing-visual {
  position: relative;
  width: 100%;
  min-height: 0;
  display: grid;
  place-items: center;
}
.landing-visual::before {
  content: '';
  position: absolute;
  width: min(740px, 70vw);
  aspect-ratio: 1;
  border-radius: 50%;
  background: var(--du-mint);
  filter: blur(1px);
}
.landing-video-frame {
  position: relative;
  z-index: 2;
  max-width: calc(100vw - 48px);
  overflow: hidden;
  border: 3px solid var(--du-ink);
  border-radius: 24px 31px 22px 29px;
  background: #050606;
  box-shadow:
    9px 10px 0 var(--du-ink),
    0 30px 80px rgba(18, 32, 31, 0.18);
  transform: rotate(1.2deg);
  will-change: width;
}
.landing-video {
  display: block;
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
}
.landing-video-frame::after {
  content: '';
  position: absolute;
  inset: 7px 6px 5px 8px;
  pointer-events: none;
  border: 2px solid rgba(255, 255, 255, 0.75);
  border-radius: 19px 26px 18px 23px;
}

.landing-paths {
  position: relative;
  max-width: 1240px;
  margin: 0 auto;
  padding: 104px 40px 124px;
}
.landing-paths::before {
  content: '';
  position: absolute;
  width: 440px;
  height: 440px;
  top: 30px;
  left: -300px;
  border-radius: 50%;
  background: rgba(185, 231, 208, 0.22);
  filter: blur(70px);
  pointer-events: none;
}
.landing-paths__heading {
  position: relative;
  display: grid;
  grid-template-columns: 1fr minmax(320px, 0.68fr);
  gap: 88px;
  align-items: end;
}
.section-kicker--dark {
  color: var(--du-coral);
}
.landing-paths h2 {
  max-width: 620px;
  margin: 12px 0 0;
  font-family: var(--du-display);
  font-size: clamp(40px, 4.8vw, 64px);
  font-weight: 700;
  letter-spacing: -0.045em;
  line-height: 1;
}
.landing-paths__heading > p {
  margin: 0 0 5px;
  color: var(--du-ink-soft);
  font-size: 17px;
  line-height: 1.65;
}
.landing-paths__grid {
  position: relative;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-top: 62px;
}
.landing-path-card {
  position: relative;
  min-height: 430px;
  display: flex;
  flex-direction: column;
  padding: 38px 34px 34px;
  overflow: hidden;
  border: 3px solid var(--du-ink);
  border-radius: 27px 34px 25px 31px;
  color: var(--du-ink);
  text-decoration: none;
  box-shadow: 8px 9px 0 rgba(18, 32, 31, 0.14);
  transform: rotate(-0.35deg);
  transition:
    transform 0.24s ease,
    box-shadow 0.24s ease;
}
.landing-path-card:nth-child(2) {
  border-radius: 34px 25px 32px 26px;
  transform: rotate(0.35deg);
}
.landing-path-card:hover {
  transform: translate(-2px, -7px) rotate(0);
  box-shadow: 11px 15px 0 rgba(18, 32, 31, 0.16);
}
.landing-path-card--student {
  background: linear-gradient(145deg, #d9f3e6 0%, #f7fcf9 78%);
}
.landing-path-card--researcher {
  background: linear-gradient(145deg, #ffc9c2 0%, #ffe4df 46%, #fff9f7 100%);
}
.landing-path-card::before {
  content: '';
  position: absolute;
  inset: 8px 7px 6px 9px;
  z-index: 0;
  border: 2px solid rgba(18, 32, 31, 0.2);
  border-radius: 22px 29px 20px 27px;
  pointer-events: none;
}
.landing-path-card::after {
  content: '';
  position: absolute;
  width: 220px;
  height: 220px;
  right: -72px;
  top: -82px;
  border: 1px solid rgba(18, 32, 31, 0.1);
  border-radius: 50%;
  box-shadow:
    0 0 0 36px rgba(255, 255, 255, 0.2),
    0 0 0 72px rgba(255, 255, 255, 0.11);
}
.landing-path-card__top {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.landing-path-card__top > span {
  position: absolute;
  top: -57px;
  right: 2px;
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border: 3px solid var(--du-ink);
  border-radius: 48% 52% 47% 53%;
  color: var(--du-ink);
  background: var(--du-surface);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  box-shadow: 3px 3px 0 rgba(18, 32, 31, 0.14);
  transform: rotate(4deg);
}
.landing-path-card__icon {
  position: relative;
  z-index: 1;
  width: 62px;
  height: 62px;
  display: grid;
  place-items: center;
  border: 2px solid var(--du-ink);
  border-radius: 18px 15px 20px 14px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 4px 4px 0 rgba(18, 32, 31, 0.16);
  transform: rotate(-2deg);
}
.landing-path-card--researcher .landing-path-card__icon {
  transform: rotate(2deg);
}
.landing-path-card__icon :deep(.hand-icon) {
  width: 34px;
  height: 34px;
}
.landing-path-card__content {
  position: relative;
  z-index: 1;
  margin-top: 52px;
}
.landing-path-card__content > span {
  color: var(--du-ink-soft);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.landing-path-card h3 {
  margin: 10px 0 12px;
  font-family: var(--du-display);
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.025em;
}
.landing-path-card p {
  max-width: 420px;
  margin: 0;
  color: var(--du-ink-soft);
  font-size: 15px;
  line-height: 1.6;
}
.landing-path-card__features {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 24px;
}
.landing-path-card__features span {
  padding: 7px 10px;
  border: 1px solid rgba(18, 32, 31, 0.1);
  border-radius: 999px;
  color: var(--du-ink-soft);
  background: rgba(255, 255, 255, 0.45);
  font-size: 11px;
  font-weight: 700;
}
.landing-path-card__action {
  position: relative;
  z-index: 1;
  width: fit-content;
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: auto;
  padding: 12px 16px;
  border: 2px solid var(--du-ink);
  border-radius: 13px 17px 12px 16px;
  color: var(--du-ink);
  background: white;
  font-size: 13px;
  font-weight: 800;
  box-shadow: 4px 4px 0 var(--du-ink);
  transform: rotate(-0.6deg);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}
.landing-path-card__action :deep(.hand-icon) {
  width: 22px;
  height: 22px;
  transition: transform 0.2s ease;
}
.landing-path-card:hover .landing-path-card__action {
  box-shadow: 2px 2px 0 var(--du-ink);
  transform: translate(2px, 2px) rotate(0);
}
.landing-path-card:hover .landing-path-card__action :deep(.hand-icon) {
  transform: translateX(4px) rotate(4deg);
}
.landing-section {
  position: relative;
  overflow: hidden;
  background: #0d1d1b;
  color: white;
  padding: 104px max(40px, calc((100vw - 1200px) / 2)) 112px;
}
.landing-section::before {
  content: '';
  position: absolute;
  width: 520px;
  height: 520px;
  top: -330px;
  right: -120px;
  border-radius: 50%;
  background: rgba(185, 231, 208, 0.08);
  box-shadow: 0 0 0 80px rgba(185, 231, 208, 0.025);
}
.landing-section::after {
  content: '';
  position: absolute;
  width: 240px;
  height: 240px;
  bottom: -170px;
  left: -80px;
  border-radius: 50%;
  background: rgba(255, 107, 82, 0.08);
  filter: blur(2px);
}
.landing-section__intro {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
  gap: 72px;
  align-items: start;
}
.section-index {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(255, 107, 82, 0.38);
  border-radius: 12px;
  color: var(--du-coral);
  background: rgba(255, 107, 82, 0.08);
  font-size: 11px;
  font-weight: 800;
}
.section-kicker {
  color: var(--du-mint);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}
.landing-section h2 {
  max-width: 570px;
  margin: 0;
  font-family: var(--du-display);
  font-size: clamp(42px, 4.5vw, 64px);
  font-weight: 700;
  letter-spacing: -0.045em;
  line-height: 0.98;
}
.landing-section__intro > p {
  max-width: 500px;
  margin: 30px 0 0;
  color: rgba(255, 255, 255, 0.62);
  font-size: 17px;
  line-height: 1.72;
}
.landing-steps {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  margin-top: 68px;
}
.landing-step {
  position: relative;
  min-height: 330px;
  display: flex;
  flex-direction: column;
  padding: 34px 28px 28px;
  overflow: visible;
  border: 2px solid rgba(255, 255, 255, 0.72);
  border-radius: 20px 27px 19px 25px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.025));
  box-shadow: 6px 7px 0 rgba(185, 231, 208, 0.2);
  transform: rotate(-0.35deg);
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease,
    background 0.22s ease;
}
.landing-step:nth-child(2) {
  border-radius: 27px 20px 26px 21px;
  transform: rotate(0.4deg);
}
.landing-step:nth-child(3) {
  transform: rotate(-0.2deg);
}
.landing-step::before {
  content: '';
  position: absolute;
  inset: 7px 6px 6px 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px 22px 15px 21px;
  pointer-events: none;
}
.landing-step:hover {
  transform: translate(-2px, -6px) rotate(0);
  box-shadow: 9px 12px 0 rgba(185, 231, 208, 0.24);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.09), rgba(255, 255, 255, 0.04));
}
.landing-step__top {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  color: var(--du-mint);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.1em;
}
.landing-step__top > span {
  position: absolute;
  top: -25px;
  left: 24px;
  width: 51px;
  height: 51px;
  display: grid;
  place-items: center;
  border: 2px solid var(--du-mint);
  border-radius: 49% 51% 46% 54%;
  color: #0d1d1b;
  background: var(--du-mint);
  box-shadow: 3px 3px 0 rgba(185, 231, 208, 0.22);
  transform: rotate(-5deg);
}
.landing-step__top :deep(.hand-icon) {
  width: 48px;
  height: 48px;
  padding: 9px;
  border: 2px solid currentColor;
  border-radius: 13px 17px 12px 16px;
  background: rgba(185, 231, 208, 0.08);
  transform: rotate(2deg);
}
.landing-step:nth-child(2) .landing-step__top :deep(.hand-icon) {
  transform: rotate(-3deg);
}
.landing-step:nth-child(3) .landing-step__top :deep(.hand-icon) {
  transform: rotate(4deg);
}
.landing-step h3 {
  margin: auto 0 16px;
  padding-top: 60px;
  font-family: var(--du-display);
  font-size: clamp(25px, 2vw, 31px);
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: 1.08;
}
.landing-step p {
  max-width: 330px;
  margin: 0;
  color: rgba(255, 255, 255, 0.58);
  font-size: 15px;
  line-height: 1.65;
}
.landing-statement {
  position: relative;
  display: grid;
  grid-template-columns: 70px 1fr auto;
  gap: 30px;
  align-items: center;
  max-width: 1200px;
  margin: 96px auto 112px;
  padding: 64px;
  border: 3px solid var(--du-ink);
  border-radius: 27px 34px 25px 31px;
  background: var(--du-mint);
  box-shadow: 8px 9px 0 rgba(18, 32, 31, 0.14);
  transform: rotate(-0.2deg);
}
.landing-statement::after {
  content: '';
  position: absolute;
  inset: 8px 7px 6px 9px;
  border: 2px solid rgba(18, 32, 31, 0.18);
  border-radius: 22px 29px 20px 27px;
  pointer-events: none;
}
.landing-statement__mark {
  position: relative;
  z-index: 1;
  align-self: start;
  color: var(--du-coral);
  font-family: Georgia, serif;
  font-size: 92px;
  line-height: 0.8;
}
.landing-statement__copy {
  position: relative;
  z-index: 1;
}
.landing-statement__copy > span {
  color: var(--du-ink-soft);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.landing-statement__copy p {
  max-width: 710px;
  margin: 12px 0 0;
  font-family: var(--du-display);
  font-size: clamp(27px, 3vw, 42px);
  font-weight: 700;
  line-height: 1.16;
  letter-spacing: -0.03em;
}
.landing-secondary-action {
  position: relative;
  z-index: 1;
  min-height: 54px;
  padding: 0 22px;
  border: 2px solid var(--du-ink);
  border-radius: 15px 18px 13px 17px;
  color: var(--du-ink) !important;
  background: white !important;
  font-weight: 800;
  box-shadow: 5px 5px 0 var(--du-ink);
  transform: rotate(0.7deg);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}
.landing-secondary-action:hover {
  box-shadow: 2px 2px 0 var(--du-ink);
  transform: translate(3px, 3px) rotate(0);
}
.landing-statement__mark {
  color: #ef3f36;
}
@media (max-width: 900px) {
  .landing-hero {
    padding-inline: 0;
  }
  .landing-visual {
    min-height: 0;
  }
  .landing-paths {
    padding-inline: 24px;
  }
  .landing-paths__heading {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  .landing-paths__grid {
    grid-template-columns: 1fr;
  }
  .landing-section {
    padding-inline: 24px;
  }
  .landing-section__intro {
    grid-template-columns: 54px 1fr;
  }
  .landing-section__intro > p {
    grid-column: 2;
    margin-top: 4px;
  }
  .landing-steps {
    grid-template-columns: 1fr;
    gap: 14px;
  }
  .landing-step {
    min-height: 250px;
  }
  .landing-step h3 {
    padding-top: 48px;
  }
  .landing-statement {
    grid-template-columns: 50px 1fr;
    margin-inline: 24px;
    padding: 48px 36px;
  }
  .landing-secondary-action {
    grid-column: 2;
    justify-self: start;
    margin-top: 12px;
  }
}
@media (max-width: 560px) {
  .landing-hero {
    padding-top: 52px;
    padding-bottom: 64px;
  }
  .landing-title {
    font-size: 50px;
  }
  .landing-actions {
    align-items: flex-start;
    flex-direction: column;
    gap: 20px;
  }
  .landing-primary-action {
    width: 100%;
  }
  .landing-visual {
    min-height: 330px;
  }
  .landing-video-frame {
    border-radius: 20px;
    transform: none;
  }
  .landing-paths {
    padding-top: 72px;
    padding-bottom: 80px;
  }
  .landing-paths__grid {
    margin-top: 38px;
  }
  .landing-path-card {
    min-height: 350px;
    padding: 26px;
  }
  .landing-section {
    padding-top: 76px;
    padding-bottom: 82px;
  }
  .landing-section__intro {
    display: block;
  }
  .section-index {
    margin-bottom: 24px;
  }
  .landing-section__intro > p {
    margin-top: 24px;
  }
  .landing-steps {
    margin-top: 42px;
  }
  .landing-step {
    min-height: 270px;
    padding: 24px;
  }
  .landing-statement {
    display: block;
    margin: 64px 16px 80px;
    padding: 38px 26px;
  }
  .landing-statement__mark {
    height: 58px;
  }
  .landing-secondary-action {
    width: 100%;
    margin-top: 32px;
  }
}
</style>
