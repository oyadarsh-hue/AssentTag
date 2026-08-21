# AssentTag — Design System & Motion Specification ("The Veil")

## 1. Token System (CSS Variables)

```css
:root {
    --void:      #05070B;  /* Deep abyssal base background */
    --carbon:    #0C111A;  /* Raised surface containers & card fills */
    --haze:      #16202E;  /* Subdued borders, hairlines, & inset panels */
    --signal:    #2DE2E6;  /* Primary cyan — verification, active, allowed */
    --assent:    #B14AED;  /* Secondary violet — identity, consent state */
    --redact:    #FF4D6D;  /* Destructive alert — purge, blocked, mismatch */
    --paper:     #E8EDF5;  /* High-contrast primary typography */
    --mute:      #7C8AA0;  /* Secondary text & labels */
    
    --grad-primary: linear-gradient(135deg, var(--signal) 0%, var(--assent) 100%);
}
```

> **Strict Rule**: The `--signal → --assent` 135° gradient is used exclusively on the primary CTA and the active navigation pill indicator.

---

## 2. Type System & Pairing

- **Display**: `Space Grotesk` (600/700 weight, `-0.03em` tracking). Used for headlines and section headers with per-character blur resolution.
- **Body**: `Inter` (400/500 weight, `1.65` line height). Used for descriptive copy and interface elements.
- **Data / Eyebrow / Code**: `JetBrains Mono` (uppercase, `0.14em` tracking, 11–12px). Used for vector metrics, threshold readouts, coordinates, and status logs.
- **Fluid Scale**: 12px / 14px / 16px / 20px / 28px / 40px / 64px / 96px (clamped fluidly).

---

## 3. Surface Language & Spatial Grid

- **Borders & Radius**: `1px solid var(--haze)`, `border-radius: 14px`.
- **Glass Panel**: `background: rgba(12, 17, 26, 0.72); backdrop-filter: blur(20px) saturate(180%);`.
- **Background Texture**: 3% opacity inline SVG noise grain (`feTurbulence`) across the viewport + 60×60px hairline grid at 4% opacity behind the hero section.

---

## 4. The Signature Moment: "The Veil"

Everything arrives obscured and is revealed only by verified consent:
1. **Per-character Headline Unblur**: Headlines render with `filter: blur(18px)` and a brightness ramp that resolves on scroll-in (staggered by 25ms per character).
2. **Radial Consent Lens**: Hero imagery displays a subtle dark/blurred filter. A cursor-following 220px lens clears the blur locally via GPU-composited CSS `mask-image` & `backdrop-filter`.
3. **Pinned Scroll Demo**: A 400vh scroll-pinned stage sequence (`01 DETECT` → `02 MATCH` → `03 BLUR` → `04 NOTIFY` → `05 REVEAL`). Face blurs are applied instantly in RAM, and consent is the explicit mechanism that lifts the blur on targeted faces.

---

## 5. Aesthetic Risk Statement

> **Aesthetic Risk**: We committed to a pitch-dark, highly technical biometric terminal theme (`--void`) with zero decorative emojis or stock illustration fluff, relying entirely on real-time canvas point clouds, KaTeX mathematical formulas, and live CSS Gaussian filters.
> **Why**: Social privacy platforms often resort to friendly cartoon mascot tropes; AssentTag's mission is cryptographic identity protection, so the design needed to command authority and technical authenticity like a high-level security command center.
