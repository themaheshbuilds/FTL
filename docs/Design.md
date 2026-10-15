# LinkForge - UI/UX Design Specification

## 1. Design Philosophy

LinkForge should feel:

- **Fast & Responsive:** Instant visual feedback for user interactions.
- **Clean & Focused:** Minimalist aesthetic prioritizing the task at hand.
- **Modern & Subtle:** Curated neutral color palette with refined indigo accents.
- **Accessible & Intuitive:** One primary action per view; no intimidating technical jargon.

Avoid:
- Generic SaaS templates
- Distracting multi-color gradients
- Overloaded dashboards
- Jarring animations
- Wall-of-text instructions

---

## 2. Brand & Visual Identity

- **Name:** LinkForge
- **Tagline:** One Link. Any File.
- **Color Palette (Peach Glow Glassmorphism):**
  - Peach Canvas: `#fff5eb` (warm, soft peach backdrop with apricot and peach-blush ambient mesh)
  - Yellow / Orange: Primary Brand & CTAs (`#f97316` / `#f59e0b` / `#fbbf24`)
  - White: Frosted Glass Cards, Clean Surfaces & Button Text (`#ffffff`, `rgba(255, 255, 255, 0.88)`)
  - Sky Blue: Active Nav Tabs, Focus Glows & Badges (`#0ea5e9` / `#38bdf8` / `#0284c7`)
  - Green: Success Badges, Ready Checkmarks & Verified Actions (`#10b981` / `#16a34a`)
  - Red: Error Icons, Alerts & Destructive/Clear Actions (`#ef4444` / `#dc2626`)
  - Charcoal Typography: `#1c1917` (ensures optimal readability and contrast on peach surfaces)
- **Typography:**
  - Headings & Body: `'Plus Jakarta Sans'`, sans-serif
  - Monospace / Badges / Filenames: `'JetBrains Mono'`, monospace

---

## 3. Navigation & Separate Page Architecture

LinkForge utilizes dedicated, specialized HTML templates with unified top pill navigation:

- **Link Downloader:** Rendered at `/` and `/index` via `templates/index.html` (controller: `static/js/downloader.js`)
- **File Converter:** Rendered at `/converter` via `templates/converter.html` (controller: `static/js/converter.js`)

Navigation Header Structure:
- Brand Logo with glowing lightning bolt icon
- Mode tabs with capsule pill styling and active glow:
  - `[ 🔗 Link Downloader ]` (links to `/`)
  - `[ ⇄ File Converter ]` (links to `/converter`)
- Modals for About and Supported Platforms / Formats

---

## 4. Link Downloader View Layout

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          One Link. Any File.                           │
│                 Extract & package files from any link                  │
│                                                                        │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ 🔗 [ https://instagram.com/p/...                 ] [Paste] [Clear] │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                          [ Analyze Link → ]                            │
│                                                                        │
│   [YouTube] [Instagram] [TikTok] [Reddit] [X] [LinkedIn] [Direct]      │
└────────────────────────────────────────────────────────────────────────┘
```

### Downloader States
1. **Initial / Hero:** Clean input bar, clipboard paste button, platform chips.
2. **Loading State:** Spinner animation with 3 sequential steps:
   - Checking platform
   - Detecting content type
   - Finding available media
3. **Result State:**
   - Platform badge and content type pill
   - Media preview container (thumbnail, image carousel, or video player)
   - Custom filename field
   - Caption toggle (`Without Caption` vs `With Caption`)
   - Video quality selector (when video is detected)
   - Dynamic format action buttons (`[PDF]`, `[ZIP]`, `[MP4]`, `[Audio]`, `[DOCX]`)
4. **Success State:** Green checkmark, filename, file size, download button, 30-minute expiry notice.
5. **Error State:** Human-readable access explanation with "Try Another Link" reset button.

---

## 5. Universal File Converter View Layout

```text
┌────────────────────────────────────────────────────────────────────────┐
│                       Universal File Converter                         │
│               Transform files directly on your machine                 │
│                                                                        │
│        [⚡ All Tools]  [📄 Documents]  [🎬 Video & Audio]  [🖼️ Images]  │
│                                                                        │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│ │ 📄 PDF to Images │  │ 🖼️ Images to PDF │  │ 📝 DOCX to PDF   │  ...  │
│ │ [Select Tool →]  │  │ [Select Tool →]  │  │ [Select Tool →]  │       │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘       │
└────────────────────────────────────────────────────────────────────────┘
```

### Interactive Workspace Card
Selecting any tool opens the workspace card with smooth scrolling:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ [← Back to Tools]                                                      │
│ 📄 PDF to Images — Extract pages into high-resolution JPG or PNG       │
│                                                                        │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ 📁 Drag & drop your file(s) here, or browse files                  │ │
│ │    Local processing • Fast, secure & private                       │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│ Staged: [ document.pdf (2.4 MB) ✕ ]                                   │
│                                                                        │
│ Output Format: [ JPG Images (.jpg) ▼ ]   Custom Name: [ my_pages     ] │
│                                                                        │
│                                              [ Convert File Now ⚡ ]   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Converter UI States

1. **Catalog State (Empty):** Grid of tool cards filtered by category pills (`all`, `docs`, `media`, `images`).
2. **File Selected / Staged State:**
   - Staged files appear as chips (`.selected-file-chip`) with filename, size, and remove button (`✕`).
   - Drag-and-drop zone highlights with indigo border (`.dragover`).
   - "Convert File Now" button enables dynamically.
3. **Format Selected State:** Dropdown populated exclusively with formats supported by the selected tool.
4. **Processing State:** Loader spinner displaying "Processing Conversion... Converting locally with native high-performance engines."
5. **Success State:** Checkmark badge, converted filename, formatted file size, direct download button, and "Convert Another File" reset button.
6. **Error State:** Warning badge, concise failure description, and "Try Again" retry button.

---

## 7. Responsive Breakpoints

- **Desktop (> 768px):** Centered card layout (max-width: 860px), multi-column tool cards grid, side-by-side format configuration.
- **Tablet (641px - 768px):** Two-column tool cards grid, flexible input containers.
- **Mobile (≤ 640px):**
  - Mode switcher wraps into flexible stack below the brand logo.
  - URL input form stacks vertically (`flex-direction: column`).
  - Converter configuration grid collapses to a single column.
  - Action buttons stretch to full width (`width: 100%`) for easy touch interaction.
  - Zero horizontal overflow.
