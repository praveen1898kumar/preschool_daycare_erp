# Little Millennium & Nest Daycare (Kharadi Branch)
## Enterprise Preschool & Daycare ERP & CRM Web Application

A full-fledged, production-ready web application engineered for **Little Millennium - Nest Daycare (Kharadi Branch, Pune)** with zero recurring API costs.

---

## 🌟 Key Capabilities & Features

### 1. Unified Authentication with 1-Click Role Switcher
- **Director / Super Admin Workspace**: Complete executive dashboard with live regulatory ratio dials, financial billing engine, CRM lead pipeline, inventory requisitions, and staff credential audits.
- **Teacher Classroom Engine**: Touch-friendly tablet daily sheets, bulk activity logging (10 naps in 3 seconds), browser-native Web Speech API voice dictation, and supply requests.
- **Parent Family Hub**: Instagram-style live activity and photo timeline, 100% native paperless digital enrollment packet with HTML5 Canvas digital signatures (zero DocuSign fees), online billing receipts, and direct 2-way messaging.
- **Student Gamified Portfolio**: High-contrast, vibrant visual interface with interactive digital badges, cheerful auditory fanfare chimes, and a reading bookshelf with virtual star stickers.

### 2. Central Branded Processing Loader
- An animated modal card with a pulsating official **Little Millennium Nest Daycare Kharadi** logo and a circular dual-tone spinner ring appears on all page transitions, form submissions, and database operations.

### 3. Edge-to-Edge Responsive Layout (Not Streamlit)
- Designed to utilize **100% of the browser window** (`100vw` × `100vh`).
- **Desktop**: Fluid multi-column dashboards, collapsible sidebar, top ratio ticker, split-screen lesson planners, and Kanban boards.
- **Mobile (<768px)**: Off-canvas navigation drawer, sticky thumb-friendly bottom navigation bar, large touch targets, and mobile-friendly canvas signatures.

---

## 🚀 How to Run the Web Application

### Method 1: 1-Click Batch File (Recommended on Windows)
Simply double-click:
```bat
run_app.bat
```
This automatically verifies the Python runtime, checks the database, launches the server, and opens your default browser at `http://127.0.0.1:5000`.

### Method 2: Manual Command Line
```powershell
# 1. Initialize and Seed the Database (Already pre-seeded)
C:\Python312\python.exe seed_data.py

# 2. Run the Application
C:\Python312\python.exe app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

---

## 👤 Instant Demo Logins (Available on Login Page)

| Role | Demo User | 1-Click Button | PIN Code |
| :--- | :--- | :--- | :--- |
| **Director / Admin** | Chanchal Sharma | `Director` | `1234` |
| **Teacher** | Ananya Deshmukh | `Teacher` | `3333` |
| **Parent** | Vikram Mehta | `Parent` | `7777` |
| **Student** | Aarav Mehta | `Student` | `0001` |

---

## 📂 Project Architecture

```
Pre-School and Day Care ERP and CRM/
├── app.py                     # Flask Server & Route Controllers (All 4 Portals)
├── config.py                  # Campus settings & regulatory ratio standards
├── database.py                # Relational SQLite schema & connection helpers
├── seed_data.py               # Pre-populated realistic Kharadi branch data
├── run_app.bat                # 1-Click Windows Batch launcher
├── run_app.ps1                # PowerShell launcher
├── test_app.py                # Full automated unit & integration test suite
├── static/
│   ├── css/custom.css         # Full-viewport styles, pulse loader & badge animations
│   ├── js/app.js              # Central loader engine, toast notifications & audio synth
│   ├── js/canvas_signature.js # HTML5 Canvas E-Signature Pad (Zero DocuSign fees)
│   ├── js/speech_to_text.js   # Browser-Native Voice-to-Text Dictation
│   └── img/logo.png           # Official Little Millennium Nest Daycare Kharadi Logo
└── templates/
    ├── base.html              # Full-page responsive master layout (100vw x 100vh)
    ├── auth/login.html        # Unified login & 1-Click Role Demo Switcher
    ├── admin/                 # Command center, live ratios, CRM, billing, staff, inventory
    ├── teacher/               # Classroom roster, bulk daily sheets, voice notes, lesson plans
    ├── parent/                # Live memories feed, paperless e-sign packet, statements, chat
    └── student/               # Gamified badges, audio fanfare, reading bookshelf
```
