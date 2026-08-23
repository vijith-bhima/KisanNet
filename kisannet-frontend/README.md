# KisanNet Frontend

Voice-first agricultural advisory app — built with Next.js 14 (App Router), Tailwind CSS, and Framer Motion.

## Run it

```bash
npm install
npm run dev
```

Then open http://localhost:3000

## What's here

- `/` — Home screen with the voice orb (the core interaction) and quick-access cards
- `/advisory` — Conversational advisory screen (voice query + response, follow-up chips)
- `/schemes` — Government scheme matching (PM-KISAN, PMFBY, KCC, Soil Health Card)
- `/profile` — Language picker (Telugu/Hindi/English/Tamil) + farm details

## Design system

- **Colors**: Paddy Green (primary), Turmeric Gold (accent/CTA), Soil Brown, Husk Cream (background), Monsoon Sky (info), Chili Red (alerts) — see `tailwind.config.ts`
- **Type**: Baloo Tammudu 2 (Telugu-supporting display face) for headings; Hind Guntur (named after Guntur — also Telugu-supporting) for body text
- **Images**: real farm photography from Pexels (free license, no attribution required), wired through `next/image` — see `lib/images.ts`

## Wiring to your FastAPI backend

Right now the advisory/schemes screens use static placeholder content so the UI is demoable standalone. To connect it to your actual pipeline:

1. Add a `.env.local` with `NEXT_PUBLIC_API_BASE=http://localhost:8000` (or wherever FastAPI runs)
2. Replace the static content in `app/advisory/page.tsx` and `app/schemes/page.tsx` with `fetch` calls to your endpoints
3. For the voice orb (`components/VoiceOrb.tsx`), wire the mic button to the browser's `MediaRecorder` API, stream/POST audio to your Cloud Speech-to-Text endpoint, and play back Cloud TTS responses

## Notes

- Needs a real internet connection at build/dev time to pull Google Fonts and Pexels images — this is normal and will work fine outside a sandboxed environment.
- Built mobile-first (max-width container) since that's how farmers will actually use it; deploys fine to Vercel or any Node host.
