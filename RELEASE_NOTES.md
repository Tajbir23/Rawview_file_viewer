# 🚀 RawView v3.9.6 Release Notes

**RawView v3.9.6** is the first release published from the new home at [Tajbir23/Rawview_file_viewer](https://github.com/Tajbir23/Rawview_file_viewer). Every feature is now permanently unlocked, the app no longer contacts GitHub in the background, and support has moved to Telegram.

---

## 📥 Download & Install

1. Download **`RawView_v3.9.6_Setup.exe`** from the **Assets** section below.
2. Run the installer. If Windows SmartScreen shows "Windows protected your PC", click **More info → Run anyway** (the installer is not code-signed).
3. RawView starts in the system tray. Hover over any supported file in Windows Explorer to preview it.

Already on an older version? Just run the new installer — it upgrades in place and keeps your settings.

---

## 🌟 What's New in v3.9.6

### 💎 1. Lifetime Pro for Everyone
* **No trial, no expiry**: The 7-day trial and the activation screen are gone. Every install is permanently unlocked with full Lifetime Pro access to all formats and features.
* **No license key needed**: Nothing to enter, nothing to renew.

### 🔒 2. No Background Network Calls
* **Auto-updater removed**: RawView no longer checks GitHub for updates in the background or on startup, and the "Check for Updates" menu entry and Settings section are gone. To update, download the latest installer from the Releases page.
* FTP file previews still work as before when you hover over `ftp://` items.

### 💬 3. Support on Telegram
* Support has moved from WhatsApp to the Telegram bot **[@chatGptPlusAIbot](https://t.me/chatGptPlusAIbot)**. Open it from **Settings → Telegram Support**.

---

# 🚀 RawView v3.9.5 Release Notes

**RawView v3.9.5** resolves a critical Windows file locking issue where hovering over a file (PDF, AI, Media, Office, Images) caused the file to remain locked by the process, preventing users from renaming or deleting the file in Windows Explorer ("The action can't be completed because the file is open in RawView" / `WinError 32`).

---

## 🌟 What's New in v3.9.5

### 🔓 1. Zero-Lock Immediate File Handle Release
* **Instant PDFium & PyMuPDF Closure**: Fixed leaked file handles in `PdfDecoder` and `AiDecoder`. `pdfium.PdfDocument` and `fitz.open` now execute inside strict `try...finally` blocks, immediately releasing the underlying OS file descriptors the instant preview decoding finishes.
* **COM Shell Provider Lifetime Management**: Explicitly calls `factory.Release()` and `CoUninitialize()` in `ShellImageFactory`, guaranteeing that third-party Windows shell thumbnail extensions (Adobe, Media, etc.) instantly release file locks.
* **Immediate Cache File Descriptor Release**: Ensures `DiskCache` operations cleanly close all image file descriptors using context managers.

### ⚡ 2. Seamless Windows Explorer Inline Rename Integration
* **Inline Rename (EditControl) Immunity**: When an item in Windows Explorer or Desktop is in rename mode (an `EditControl` is active or focused), RawView automatically detects it, aborts hover resolution, and clears any active hover, ensuring RawView never attempts to decode or touch a file while you are renaming it.
* **F2 Hotkey Dismissal**: Pressing `F2` (the universal Windows Rename shortcut) immediately dismisses any active hover preview and frees all media/decoder resources so Windows Explorer can enter rename mode without conflict.
* **Outside Click Auto-Dismiss**: When hover preview is unpinned, clicking the mouse (left or right click) outside the preview HUD (e.g. clicking a file to rename or right-clicking for the context menu) instantly dismisses the preview and stops any media playback.

---

# 🚀 RawView v3.9.4 Release Notes

**RawView v3.9.4** fixes a critical file resolution bug where hovering over a file (e.g. JPEG) falsely triggered previews of same-named files with different extensions (e.g. PSD) even when that format was turned off in Settings. Furthermore, v3.9.4 introduces a **0ms native Windows global hotkey (`Ctrl + \``)** and an **instant floating on-screen glassmorphic HUD pill** for ultra-responsive toggle feedback.

---

## 🌟 What's New in v3.9.4

### 🎯 1. Same-Stem File Disambiguation (PSD vs JPEG Fix)
* **Strict Disabled Format Rejection**: When basic image formats (JPG, PNG, WebP, BMP, GIF) are disabled in Settings, hovering over an image will **never** trigger a preview under any condition. RawView will immediately abort and never fall back to guessing other extensions like `.psd`.
* **Identical-Name Multi-Extension Disambiguation**: When multiple files share the exact same base name in the same folder (e.g. `mockup.psd` and `mockup.jpg`):
  * RawView inspects Windows Explorer's item type (`ItemType` and `HelpText` / InfoTip) to match the exact file under the cursor.
  * Compares exact file size (`Size: 203 KB` vs `Size: 93.6 MB`) against disk files so it never mixes them up.
* **Window-Scoped Folder Search**: When hovering an item in Windows Explorer, candidate folders are strictly scoped to that specific window and its own tabs. Files in one Explorer window will never resolve to files in a different open Explorer window.

### ⚡ 2. Zero-Latency Native Global Hotkey (`Ctrl + \``)
* **Native Windows Kernel Hotkey**: Registered via `RegisterHotKey` and `QAbstractNativeEventFilter`, intercepting `Ctrl + \`` with **0ms latency** directly from the Windows message loop.
* **Independent of Timer Polling**: The shortcut triggers immediately regardless of mouse movement, UI Automation resolution, or system load.

### 👁 3. Instant On-Screen Status HUD Badge (<5ms)
* **Floating Glassmorphic Pill Toast**: Completely replaces the sluggish 2–4 second delay of Windows Action Center balloon toasts with an instant, modern floating HUD pill centered at the top of your screen:
  * **Active**: Emerald glowing indicator + `RawView Hover Preview: Active` (`Ctrl + \``)
  * **Paused**: Amber indicator + `RawView Hover Preview: Paused` (`Ctrl + \``)
* **Smooth Micro-Animation**: Fades in within 120ms, stays for 1 second, and smoothly fades out with zero focus stealing or workflow interruption.

---

# 🚀 RawView v3.9.3 Release Notes

**RawView v3.9.3** introduces multi-page thumbnail sidebar navigation for **PDF** and **Word documents**, enabling users to pin with `Space` and seamlessly browse through any document page with thumbnails or keyboard controls. Additionally, v3.9.3 incorporates a built-in **Bijoy/SutonnyMJ-to-Unicode engine** that perfectly resolves corrupted Bengali typography in Word documents into clean, authentic Bengali text.

---

## 🌟 What's New in v3.9.3

### 📑 1. Left Thumbnail Sidebar for Multi-Page PDF & Word Documents
* **Visual Page Thumbnails**: For multi-page PDFs and Word files (`.docx`, `.doc`, `.rtf`), RawView automatically renders a vertical left sidebar displaying real miniature page previews with page number badges (`Page 1`, `Page 2`, `Page 3`...).
* **Space to Pin & Browse**: Press `Space` to pin the preview window into an interactive state, allowing you to click any page card to inspect it immediately.
* **Keyboard Page Navigation**: When pinned, navigate between document pages using `Down` / `Up` or `PageDown` / `PageUp`.
* **Dynamic Active State**: The active page card highlights with a vivid `#38BDF8` border and accent background glow.
* **Zero Overhead on Single-Page Files**: The sidebar automatically hides for single-page documents, images, and videos, keeping the preview window clean and compact.

### 🇧🇩 2. Authentic Bengali Font & SutonnyMJ/Bijoy Typography Engine
* **Full Bijoy to Unicode Translation**: Resolves corrupted ASCII letters in legacy SutonnyMJ/Bijoy Word documents (e.g. `wemwgjø...` renders as `বিসমিল্লাহির রাহমানির রাহিম`, `Ò‡`vKvb Ni...` renders as `“দোকান ঘর ভাড়ার চুক্তিপত্র দলিল”`).
* **Comprehensive Bengali Conjunct & Modifier Support**: Accurately handles complex conjuncts (`ক্ষ`, `জ্ঞ`, `ঞ্চ`, `ঞ্জ`, `ত্র`, `দ্ব`, `দ্ম`, `ষ্ট`, `ষ্ঠ`, `ষ্ণ`, `হ্ম`, `হু`, `স্ব`, `স্ক`, `স্ত`, `স্থ`, `স্ন`, `স্প`, `স্ম`, `ল্ল`, `শ্ব`, `শ্ম`, `ন্দ`, `ন্ধ`, `ন্ত`, `ম্প`, `ম্ব`, `ম্ভ`, `ম্ম`, `ক্ত`, `চ্চ`, `চ্ছ`, `ত্ত্ব`, `ম্ন`, `ফ্ল`), pre-kars (`ি`, `ে`, `ৈ`, `ো`, `ৌ`), post-kars, and ref (`র্`).
* **Windows Bengali Typography Stack**: Integrates native Bengali font fallbacks (`Kalpurush`, `SolaimanLipi`, `Nikosh`, `Nirmala UI`, `Vrinda`), ensuring crisp, legible, and authentic Bengali reading.

### ⚡ 3. High-Speed On-Demand Vector PDF Rasterization
* **Instant First-Page & Thumbnail Cache**: Multi-page PDFs render page 1 and all miniature page thumbnails in milliseconds, loading subsequent full-resolution vector pages on demand when clicked.

---

# 🚀 RawView v3.9.2 Release Notes

**RawView v3.9.2** delivers a major upgrade to Microsoft Office previewing — introducing native visual rendering for **Word documents (.docx, .doc, .rtf)** and **Excel spreadsheets (.xlsx, .xls, .csv)**. Instead of displaying static metadata overview cards, RawView now parses and renders real document pages, styled paragraphs, tables, and spreadsheet cell grids with near-instant responsiveness (~28ms–100ms).

---

## 🌟 What's New in v3.9.2

### 📄 1. True Visual Word Document Rendering (.docx, .doc, .rtf)
* **Real In-Document Content**: Parses `word/document.xml` to extract actual headings, paragraphs, bold/italic text runs, bullet lists, and tables with borders.
* **Realistic A4 / US Letter Canvas**: Renders onto a clean 850×1100 px white document sheet featuring subtle paper borders, top Word Blue accent (`#2563EB`), and a descriptive footer.
* **Legacy Format Support**: Seamlessly parses vintage Word 97–2003 (`.doc`) binary text streams and Rich Text Format (`.rtf`) into formatted document pages.

### 📊 2. Authentic Excel Spreadsheet Grid View (.xlsx, .xls, .csv)
* **Real Spreadsheet Grid**: Parses workbook sheets, shared strings, and worksheet rows/cells to render an interactive-looking 960×680 px spreadsheet grid.
* **Column Coordinates & Row Numbers**: Standard Excel column letters (`A`, `B`, `C`, `D`...) and row numbers (`1`, `2`, `3`...) with subtle gridlines and alternating row shading (`#FFFFFF` / `#F9FAFB`).
* **Intelligent Data Alignment**: Automatically formats numbers as right-aligned with proper cell padding, and text as left-aligned.
* **Excel Brand Banner & Sheet Tabs**: Features a clean Excel green ribbon (`#107C41`) showing workbook filename, active sheet name, row/col stats, and bottom sheet tab indicators (`[Sheet1] [Sheet2]`).
* **CSV & Legacy XLS**: Fully renders CSV data and legacy `.xls` files directly into the same clean spreadsheet grid.

### 📽️ 3. PowerPoint Slide Canvas Renderer (.pptx, .ppt)
* **Slide 1 Visual Presentation**: When files lack pre-saved thumbnail images, RawView automatically parses `ppt/slides/slide1.xml` to extract slide titles, subtitles, and key bullet points onto a 16:9 widescreen presentation canvas (960×540 px).

---

# 🚀 RawView v3.9.1 Release Notes

**RawView v3.9.1** is a massive milestone release featuring a sleek tabbed Settings & Shortcuts interface with vector checkmarks, support for legacy Adobe Illustrator & Microsoft Office file formats, optional preview support for standard and web images (JPG, PNG, WebP, GIF, ICO, BMP - off by default), and pre-checked Windows boot autostart in the setup installer.

---

## 🌟 What's New in v3.9.1

### ✅ 1. Crisp Vector Checkmarks (`✓`) in Preferences
* **Replaced Solid Blue Blocks**: Checkbox indicators across the Settings interface now feature a crisp, vector checkmark tick icon (`assets/checkmark.svg`) instead of a solid colored block, giving a modern and polished feel.
* **Refined Hover & Active States**: Smooth visual feedback with `#0284C7` background, `#38BDF8` border, and high-contrast white ticks.

### 🗂️ 2. Dual-Tabbed Settings Hub with Interactive Shortcuts Guide
* **`⚙️ Preferences` Tab**: Clean, organized configuration for Lifetime Pro activation, hover responsiveness slider (40ms–350ms), boot autostart, and categorized file format toggles.
* **`⌨️ Shortcuts & Controls` Tab**: Dedicated, visually rich instruction panel documenting all 9 keyboard and mouse controls with `<kbd>` badges and action summaries:
  * `Ctrl + \`` — Toggle preview service on/off system-wide
  * `Space` — Pin/unpin preview window or play/pause live video
  * `Mouse Wheel` — Smooth zoom in/out (50% to 800%)
  * `Left-Click + Drag` — Pan across zoomed canvas
  * `Double-Click` — Reset zoom & pan to 100% default fit
  * `Ctrl + C` — Copy full-resolution preview to Windows clipboard
  * `Ctrl + O` or `Enter` — Open file in default application
  * `Esc` — Immediately close and dismiss preview
  * `Mouse Hover Away` — Smooth zero-lag auto-dismissal when unpinned

### 🖼️ 3. Standard & Web Image Support (Disabled by Default)
* **New Format Support**: Instant hardware-accelerated previews for `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.ico`, and `.bmp`.
* **Off by Default**: Per user preference, standard images are **strictly unchecked by default** in settings so that RawView remains focused on specialized graphics and documents unless users explicitly check them.
* **High-Performance Rendering**: Includes EXIF auto-orientation, RGBA alpha checkerboard backdrop, downsampling optimization for large multi-megapixel photos, and GIF frame count / ICO multi-size metadata.

### 🏛️ 4. Legacy Adobe Illustrator & Microsoft Office Support
* **Illustrator v1–v8 (Legacy PostScript/EPS)**: Binary EPS header extraction (`0xC5D0D3C6` / `0xC6D3D0C5`) retrieving embedded TIFF previews for vintage Illustrator artwork without PDF compatibility streams.
* **Legacy Word (`.doc`) & RTF**: Binary text stream extraction providing readable document preview cards when Windows shell preview handlers are unavailable.
* **Legacy Excel (`.xls`)**: BIFF8 record parsing to extract sheet names and workbook metadata.
* **Two-Stage Shell Extraction**: Queries `IExtractImage` with full pipeline rendering before falling back to static icons.

### 🚀 5. Setup Installer Autostart Checked by Default
* **Pre-Checked Boot Option**: Updated Inno Setup installer script (`Flags: checkedonce`) so "Start RawView automatically when Windows boots" is pre-toggled during installation while remaining fully untickable by the user.

---

# 🚀 RawView v3.1.7 Release Notes

**RawView v3.1.7** introduces a major vector rendering overhaul for **Adobe Illustrator (.AI)** files — delivering crystal-clear 300 DPI vector previews, eliminating low-res thumbnail dependencies, fixing white-canvas false-blank detection, and adding high-definition Illustrator branded overview cards for unstreamed files.

---

## 🌟 What's New in v3.1.7

### 🎨 1. Vector-First Rendering for Adobe Illustrator (.AI)
* **Crystal-Clear Vector Quality**: Illustrator files now prioritize native vector rasterization via PyMuPDF and PDFium at up to 1440px and 300 DPI. Previews are razor-sharp, allowing users to zoom in from 50% up to 800% to inspect typography, curves, and fine details.
* **Eliminated False Overflow Skipping**: Previously, files with artwork, bleeds, or crop marks extending slightly outside the artboard (`has_overflow = True`) had vector rendering skipped completely, forcing RawView into low-res thumbnails. Vector rasterization is now always prioritized whenever vector elements exist.
* **Multi-Artboard Discovery**: Automatically inspects multi-artboard Illustrator documents, reporting active artboard details (e.g. `Artboard 1 of 4`) in the preview badge.

### 🔍 2. Precision Area-Downsampled Blank Canvas Detection
* **Eliminated False-Blank Rejections**: Previously, small vector graphics (such as garment neck labels, logos, or icons) occupying less than 5% of a white artboard were falsely flagged as "blank pages" by a naive 95% brightness threshold.
* **Area-Averaged Luminance Verification**: Replaced grid-based sampling with bilinear area downsampling. Pure blank pages are rejected cleanly, while designs with fine lines or small logos on white backgrounds render with 100% fidelity.

### 🛡️ 3. High-Definition Adobe Illustrator Overview Cards
* **Graceful Fallback for Non-PDF AI Files**: When designers save AI files with "Create PDF Compatible File" unchecked and without embedded thumbnails, RawView previously threw an unhandled exception with no preview window.
* **Dark Glassmorphic Overview Card**: RawView now parses PostScript header metadata (`%%BoundingBox`, `%%HiResBoundingBox`, `%%Creator`, `%%Title`) to render a sleek, branded Adobe Illustrator Overview Card (Amber `#FF9A00` badge, artboard canvas dimensions, creator version, file size, and descriptive status).

### ⚙️ 4. Thread-Safe Windows Shell Image Factory
* **Worker Thread COM Initialization**: Explicitly initializes COM apartments (`CoInitialize`) and safely frees GDI bitmap handles in background worker threads, preventing intermittent `E_INVALIDARG` failures.
* **Connected Worker Error Signals**: Connected background decode error signals to the application controller to eliminate silent drops and maintain robust logging.

---

# 🚀 RawView v3.1.6 Release Notes

**RawView v3.1.6** brings pixel-perfect high-zoom rendering and a new global `Ctrl+\`` keyboard shortcut to toggle hover previews on/off instantly from anywhere.

---

## 🌟 What's New in v3.1.6

### 🔍 1. Fixed Zoom Blur — Pixel-Perfect High-Zoom Rendering
* **Native Resolution Cap**: Zoom scaling is now capped at the source image's native pixel dimensions. Previously, zooming beyond the display-fit base size caused Qt to upscale beyond available pixel data, producing bilinear blur artifacts.
* **Adaptive Transformation Mode**: Zoom levels above 200% now use `FastTransformation` (nearest-neighbor) for crisp, pixel-perfect rendering — matching behavior in professional tools like Photoshop and Figma. Zoom levels at or below 200% continue to use `SmoothTransformation` (bilinear anti-aliasing) for a pleasant downscale appearance.
* **Impact**: All image formats (PSD, PSB, AI, EPS, PDF, TIFF, RAW, and more) benefit from sharp, clear zoom rendering from 50% up to 800%.

### ⌨️ 2. Global `Ctrl+\`` Hotkey — Instant Preview Toggle
* **System-Wide On/Off Toggle**: Press `Ctrl+\`` from anywhere on Windows (Explorer, Desktop, any window) to instantly enable or disable hover previews without opening the tray menu.
* **Tray Sync**: The System Tray menu checkbox automatically reflects the new state after each toggle.
* **Tray Notification**: A brief balloon notification confirms the current state — ✅ *Hover Preview Enabled* or ⏸ *Hover Preview Disabled*.
* **Auto-Dismiss**: Disabling via hotkey immediately dismisses any currently visible preview HUD.

---

# 🚀 RawView v3.1.5 Release Notes

**RawView v3.1.5** fixes a critical video source binding bug where `QMediaPlayer` attempted to load raw `.aep` / `.prproj` binary project paths instead of the resolved linked MP4/MOV footage, restoring instant, smooth 60 FPS live video playback for Adobe projects.

---

## 🌟 What's New in v3.1.5

### 🎬 1. Fixed Video Player Source Binding
* **Resolved Linked Video Playback Bug**: Fixed `FloatingPreviewHUD` to route the resolved `result.video_path` to `QMediaPlayer.setSource()`, eliminating black screen stalls on `.aep` and `.prproj` files.
* **Instant Footage Playback**: Linked video footages and rendered outputs (`Render/`, `Output/`, `Stock/`) now play immediately upon mouse hover with live timeline tracking.

---

# 🚀 RawView v3.1.4 Release Notes

### 🎬 1. Smart Linked Video & Footage Playback
* **Automatic Render & Output Resolution**: Discovers matching exported video files (`Render/`, `Output/`, `Export/`, or same directory) and plays them instantly in the preview HUD with 60 FPS muted looping.
* **Deep Timeline Footage Discovery**: Automatically resolves linked video footage clips (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.m4v`) referenced in the project timeline and plays them live on cursor hover.
* **Motion Graphics & Typography Visualizer**: For pure text/shape animation projects with no linked video footage, displays the high-contrast Typography & Motion Design showcase card with composition badges and layer properties.

---

# 🚀 RawView v3.1.3 Release Notes

### 🎬 1. Deep After Effects Composition & Layer Extraction
* **RIFX Project Tree Parsing**: RawView now inspects After Effects binary chunks to extract actual composition names (e.g. `50 TK`, `Outro`, `Intro Animation`) and linked footage assets.
* **Redesigned High-Definition Fallback Cards**: Upgraded to 640x420 RGB32 cards with dual-tile layout:
  * **Top Tile**: Displays numbered badges for active compositions and sequence timelines.
  * **Bottom Tile**: Displays file size, date modified, author, and linked assets with bright legible typography.
* **Eliminated Truncation & Low-Contrast Text**: Fixed clipping issues and replaced dull gray labels with vibrant, high-contrast Segoe UI typography.

---

# 🚀 RawView v3.1.2 Release Notes

### 🎯 1. Eliminated Generic Application Icon Fallbacks
* **Strict Visual Thumbnail Validation (`SIIGBF_THUMBNAILONLY`)**: Windows Shell image provider is now queried strictly for real visual page/slide thumbnails. Generic file association icons (such as upside-down Ae icons or blank paper icons) are blocked from display.
* **Embedded Slide & Document Media Extraction**: Office files (`.docx`, `.pptx`) automatically inspect embedded slide images and graphics if standalone thumbnails are not stored by Office.
* **High-Definition Creative Cloud & Office Cards**: When no visual thumbnail exists, RawView displays a dark branded overview card showing file name, sequence/document title, author, slide/sheet count, and file statistics.

---

# 🚀 RawView v3.1.1 Release Notes

### 📄 1. Microsoft Office & Document Previews
* **Microsoft Word (`.docx`, `.doc`, `.docm`, `.dotx`, `.dot`, `.rtf`)**: Zero-lag embedded OpenXML thumbnail extraction with page count, word count, document title, and author information.
* **Microsoft Excel (`.xlsx`, `.xls`, `.xlsm`, `.xlsb`, `.xltx`, `.csv`)**: Instant spreadsheet previews displaying workbook title, sheet names (`Summary`, `Revenue`, etc.), and structural metadata.
* **Microsoft PowerPoint (`.pptx`, `.ppt`, `.pptm`, `.ppsx`, `.potx`)**: Slide deck overview showing slide counts, presentation titles, and high-resolution slide thumbnails.

### 🎬 2. Adobe Video & Motion Graphics Projects
* **Adobe After Effects (`.aep`, `.aet`, `.aepx`)**: Hardware-accelerated shell thumbnail rendering with composition structure and file statistics.
* **Adobe Premiere Pro (`.prproj`, `.prset`)**: Compressed project header inspector extracting project version, active sequence names, and video format information.

### ⚙️ 3. Redesigned Scrollable Settings Hub
* **Categorized Format Preferences**: Dedicated control groups for **Graphics & Design**, **Microsoft Office & Documents**, **Adobe Video Projects**, and **Live Video Playback**.
* **Responsive Scroll Viewport**: Settings dialog now dynamically fits all monitor resolutions with smooth vertical scrolling and sticky action buttons.

---

# 🚀 RawView v2.0.5 Release Notes

### 📂 1. Comprehensive Windows 11 Multi-Tab Support
- **Full Tab Discovery**: Fixed an issue where open tabs sharing the same top-level Explorer window handle would cause non-primary tabs to fail resolution.
- **Unified Tab Candidate Search**: All folder paths belonging to open tabs in the active window are dynamically discovered and queried, guaranteeing instant previews regardless of which tab is active.

---

# 🚀 RawView v2.0.4 Release Notes

### ⚡ 1. Resilient Hover Dwell & Resolution Engine
- **Fixed Hover State Lock**: Resolved an issue where hover state checks could prevent subsequent files from triggering preview popups.
- **Position-Based Settle Detection**: Previews now resolve exactly once per settled cursor position, ensuring instant response across List, Details, Grid, Icons, and Desktop views while maintaining zero UI thread usage during dwell.

---

# 🚀 RawView v2.0.3 Release Notes

### 🎬 1. Ultra-Smooth 60 FPS Live Video Previews
- **Zero Event-Loop Starvation**: Fixed an issue where continuous 35ms UIAutomation and Shell COM queries during mouse dwell starved Qt's event loop, causing dropped frames and stuttering playback.
- **Hardware Direct3D Video Output**: Configured `QVideoWidget` with native opaque hardware paint modes without CSS rasterization bottlenecks.
- **Throttled Repaints & Layout Updates**: Throttled progress bar and timestamp updates to eliminate redundant CPU/GPU drop-shadow blur passes.
- **Sub-Millisecond Thumbnail Resolution**: Instant thumbnail cache lookups (~0.6ms) for immediate preview HUD display before seamless live video stream starts.

---

## 🚀 RawView v2.0.2 Release Notes

### 🎯 1. Fixed Blank Space / Folder Background Hover Bug
- **Precise Item Detection**: Resolved an issue where hovering the cursor over empty whitespace / background areas of a folder window in Windows Explorer would inadvertently trigger a preview if the folder name matched any file inside.
- **Strict Row Containment**: The hover engine now requires the cursor to be directly inside a valid file item (`ListItemControl`, `DataItemControl`, or `TreeItemControl`). Moving into blank background space immediately dismisses any active preview without ghosting or lingering previews.

---

### ⏳ 2. 7-Day Unlimited Free Trial Engine
- **100% Unrestricted Access**: All features (Photoshop PSD/PSB, Illustrator AI, EPS, PDF, Camera RAW, TIFF, SVG, Live Video Playback, Deep Zoom) are completely unlocked for the first 7 days.
- **Subtle Trial Countdown**: The footer cleanly displays `⏳ Trial: Xd left`.
- **Glassmorphic Pro Card (Day 8+)**: When the trial concludes, hovering over files displays an upgrade prompt with the customer's Machine Code, bKash payment info, and direct WhatsApp support launcher.

---

### 🔐 3. Hardware ID Machine-Locked 50 TK Offline Licensing
- **Windows MachineGuid Cryptography**: Automatically binds licenses to unique hardware machine codes (`RV-XXXX-XXXX-XXXX`).
- **HMAC-SHA256 Signatures**: Zero server dependency, 100% offline, zero-latency cryptographic verification.
- **Anti-Piracy**: A license key generated for one PC cannot be shared or used on any other machine.
- **Lifetime Pro**: Once activated, the license persists permanently across app updates and reboots.

---

### 💳 4. Direct bKash & WhatsApp Purchase Integration
- **bKash Personal (50 TK)**: `01756678087` with a 1-click **[📋 Copy bKash]** button.
- **WhatsApp Support**: `+1 (202) 780-6050` with a 1-click **[💬 Open WhatsApp]** button that opens WhatsApp with the customer's Machine Code pre-filled.
- **Settings Dialog Pro Section**: Clean 4-step guide for purchasing, copying codes, and activating license keys.

---

## ⌨️ Keyboard & Mouse Controls

| Action | Control | Description |
| :--- | :--- | :--- |
| **Toggle Preview On/Off** | `Ctrl + \`` | Enables or disables hover previews globally (system-wide hotkey, works anywhere) |
| **Pin Preview** | `Space` | Keeps the preview window open even when cursor moves away |
| **Play / Pause Video** | `Space` *(when pinned)* | Toggles live video playback |
| **Zoom In / Out** | `Mouse Wheel` | Smoothly zooms images and vector graphics from 50% to 800% |
| **Pan Image** | `Left-Click + Drag` | Moves the zoomed image within the viewport |
| **Reset View** | `Double-Click` | Resets zoom and pan back to 100% fitted size |
| **Copy Image** | `Ctrl + C` | Copies high-resolution preview image to Windows Clipboard |
| **Open File** | `Ctrl + O` / `Enter` | Launches the file in its default desktop application |
| **Close Preview** | `Esc` | Immediately dismisses the preview HUD |

---

## 📦 Installer Package
- **Installer**: `dist_installer/RawView_v3.1.6_Setup.exe` (~122 MB)
- **Target OS**: Windows 10 & Windows 11 (64-bit)
- **Publisher**: BlackBox THC
