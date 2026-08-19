---
name: Hope Bridge
colors:
  surface: '#f8f9ff'
  surface-dim: '#d1dbec'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eef4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dfe9fa'
  surface-container-highest: '#d9e3f4'
  on-surface: '#121c28'
  on-surface-variant: '#40484e'
  inverse-surface: '#090a0a'
  inverse-on-surface: '#eaf1ff'
  outline: '#3f0ec5'
  outline-variant: '#bfc7cf'
  surface-tint: '#00658d'
  primary: '#00658d'
  on-primary: '#ffffff'
  primary-container: '#58a4d0'
  on-primary-container: '#003850'
  inverse-primary: '#85cffd'
  secondary: '#6e5e0d'
  on-secondary: '#ffffff'
  secondary-container: '#f6df84'
  on-secondary-container: '#726212'
  tertiary: '#5d5f5f'
  on-tertiary: '#ffffff'
  tertiary-container: '#9b9c9c'
  on-tertiary-container: '#323434'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c6e7ff'
  primary-fixed-dim: '#85cffd'
  on-primary-fixed: '#001e2d'
  on-primary-fixed-variant: '#004c6b'
  secondary-fixed: '#f9e287'
  secondary-fixed-dim: '#dcc66e'
  on-secondary-fixed: '#221b00'
  on-secondary-fixed-variant: '#534600'
  tertiary-fixed: '#e2e2e2'
  tertiary-fixed-dim: '#c6c6c7'
  on-tertiary-fixed: '#1a1c1c'
  on-tertiary-fixed-variant: '#454747'
  background: '#f8f9ff'
  on-background: '#121c28'
  surface-variant: '#d9e3f4'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Be Vietnam Pro
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Be Vietnam Pro
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  button:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 48px
  xl: 80px
  container-max: 1200px
  gutter: 24px
  margin-mobile: 16px
---

## Brand & Style

The brand personality is anchored in empathy, connection, and optimism. It aims to bridge the gap between those who want to help and those in need, fostering a sense of community and shared humanity. The emotional response should be one of "gentle urgency"—a calm, trustworthy environment that encourages immediate positive action.

This design system utilizes a **Modern-Organic** style. It blends the cleanliness of corporate SaaS with the warmth of lifestyle photography and soft, tactile UI elements. By prioritizing high-quality white space and rounded forms, the interface feels accessible and non-threatening, ensuring donors of all technical abilities feel welcomed and secure.

## Colors

The palette is designed to evoke the sky and sunlight, symbolizing hope and clarity.

*   **Primary (Light Blue):** Used for main actions, headers, and brand-heavy backgrounds. It provides a sense of stability and professional trust.
*   **Secondary (Soft Yellow):** Reserved for accent moments, secondary buttons, and icons. It represents the "spark" of hope and draws the eye to key engagement points without being aggressive.
*   **Neutral:** A deep slate grey is used for body text to ensure high legibility against white and light blue backgrounds.
*   **Backgrounds:** Pure white is the primary surface color to maintain a clean, airy feel that allows photography of human stories to stand out.

## Typography

The typography strategy balances modern professionalism with a friendly, conversational tone.

*   **Headlines:** **Plus Jakarta Sans** is used for its soft, rounded terminals and contemporary feel. Large headlines should use a tight letter-spacing to appear more cohesive and impactful.
*   **Body & Labels:** **Be Vietnam Pro** offers exceptional readability and a warm, rhythmic flow that suits long-form storytelling and donation details.
*   **Hierarchy:** Use the Headline XL for hero sections to immediately establish the emotional hook. Label styles should be used sparingly for metadata or small "Impact Tags" above headlines.

## Layout & Spacing

The layout follows a **Fluid Grid** philosophy to ensure the emotional impact of the imagery is preserved on all devices.

*   **Desktop:** 12-column grid with a 1200px max-width container. Content is centered with generous 80px (XL) vertical padding between major sections to allow the brand to "breathe."
*   **Mobile:** Transitions to a single-column stack with 16px side margins. Padding between sections reduces to 48px (LG).
*   **Rhythm:** Use an 8px base unit. Component spacing (e.g., text to button) should typically be 24px (MD) to maintain clarity and prevent the interface from feeling cluttered.

## Elevation & Depth

This design system uses **Tonal Layering** combined with **Ambient Shadows** to create a sense of approachability and physical presence.

*   **Surface:** Primary background is White (#FFFFFF). Cards and containers use a very subtle 1px border in a lightened version of the Primary color (approx. 10% opacity) to define edges without adding visual weight.
*   **Shadows:** Use large, highly diffused shadows for interactive cards. Shadows should be tinted with the Primary Blue (e.g., `rgba(88, 164, 208, 0.08)`) rather than pure black to keep the UI feeling "light" and optimistic.
*   **Depth:** Lower-level elements (like input fields) should appear slightly inset or flat, while actionable elements (like donation cards) should appear elevated to invite interaction.

## Shapes

The shape language is consistently rounded to reinforce the "friendly" and "human" brand pillars.

*   **Cards & Containers:** Follow the `rounded-lg` (1rem) and `rounded-xl` (1.5rem) settings. Avoid sharp corners entirely as they can feel clinical or aggressive.
*   **Decorative Elements:** Use circular or organic "blob" shapes in the background with the Primary Blue at 5-10% opacity to break up strict horizontal lines.
*   **Images:** Photography should always feature slightly rounded corners (0.5rem minimum) to align with the UI elements.

## Components

*   **Buttons:** Primary buttons are Solid Light Blue with White text, using the `button` typography and fully rounded (pill) shapes. Secondary buttons use the Soft Yellow background with Neutral text to indicate alternative actions.
*   **Donation Cards:** These are the centerpiece. Use a White background, `rounded-xl` corners, and a soft ambient shadow. Include a progress bar in Primary Blue to show fundraising goals.
*   **Input Fields:** Use a 1.5px border in a soft grey. On focus, the border should transition to Primary Blue with a subtle outer glow (halo effect).
*   **Impact Chips:** Small, rounded labels used to categorize causes (e.g., "Education", "Food Security"). These should use the Soft Yellow background with a small icon.
*   **Interactive Heart:** The brand heart/bridge icon should be used as a "loading" state or a "Thank You" animation, pulsing gently to reinforce the emotional connection.
*   **Progress Bars:** Use a thick, rounded track (8px height) with the Primary Blue for the filled portion and a very light tint of the same blue for the track background.