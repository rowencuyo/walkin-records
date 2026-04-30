# Archivium — Walk-in Records Management System

A secure, offline desktop application for managing foreign student walk-in records, visa documentation, and enrollment tracking. Built with **Python** and **PySide6 (Qt6)**.

---

## ✨ Features

### 🔐 Security & Access
- **Login Authentication** with encrypted password storage (salted hashing)
- **Session Locking** — automatic idle timeout with manual Ctrl+L shortcut
- **Read-Only Mode** — toggle to prevent accidental edits during review
- **Audit Logging** — every action is tracked with timestamps and user info

### 📊 Dashboard
- **Real-time Analytics** — total records, enrollment breakdown, visa status overview
- **Alert Cards** — highlights expiring visas, missing documents, and system warnings
- **Recent Activity Feed** — quick access to recently viewed or edited records

### 📋 Record Management
- **Smart Search** — instantly find records by name, passport number, or any field
- **Advanced Filtering** — filter by enrollment status, visa category, or date range
- **Comprehensive Forms** — guided data entry with built-in validation
- **360° Profile View** — all student information, documents, and history in one screen
- **Pagination** — efficiently browse large datasets (25/50/100/200 per page)

### 📎 Document Storage
- **Digital Filing** — attach passports, birth certificates, transcripts, and more
- **Profile Pictures** — auto-compressed image management
- **Completeness Tracking** — monitors which required documents are missing
- **Supported Formats** — PDF, JPG, PNG, DOC/DOCX (up to 25 MB each)

### 🔔 Smart Notifications
- **Automated Visa Alerts** — warns before student visas expire (configurable threshold)
- **Missing Document Alerts** — flags incomplete student files
- **Three-Tab System** — Active → Dismissed → History lifecycle
- **Batch Controls** — mark all as read with one click

### 📤 Data Export
- **Excel Export** — generates formatted reports from a built-in Excel template
- **Date Range Selection** — export records for any time period
- **Template-Based** — preserves your office's formatting and column layout

### ⚙️ Settings
- **Idle Lock Configuration** — set timeout from 5 to 60 minutes
- **Notification Preferences** — enable/disable visa, document, and backup alerts
- **Visa Expiry Threshold** — configure how many days before expiry to alert (default: 30)
- **Account Management** — change username and password securely

---

## 🗂 Project Structure

```
walkin-records/
├── main.py                  # Application entry point
├── archivium.spec           # PyInstaller build configuration
├── WalkIn_Records_Export.xlsx# Excel export template
├── app/
│   ├── constants.py         # Enums, config values, country/visa lists
│   ├── database.py          # SQLite connection, schema, migrations
│   ├── models.py            # Data models (WalkInRecord, Document, etc.)
│   ├── services/
│   │   ├── auth_service.py          # Login & password management
│   │   ├── record_service.py        # CRUD operations for records
│   │   ├── document_service.py      # File attachment management
│   │   ├── image_service.py         # Profile picture processing
│   │   ├── export_service.py        # Excel report generation
│   │   ├── dashboard_service.py     # Analytics & activity tracking
│   │   ├── notification_service.py  # Automated alert generation
│   │   ├── preferences_service.py   # User settings (key-value store)
│   │   ├── draft_service.py         # Unsaved form draft recovery
│   │   └── completeness.py          # Document checklist validation
│   ├── ui/
│   │   ├── main_window.py           # Primary window & navigation
│   │   ├── workspace.py             # Sidebar + page stack layout
│   │   ├── theme.py                 # Colors, fonts, stylesheet
│   │   ├── pages/
│   │   │   ├── login_page.py        # Authentication screen
│   │   │   ├── lock_screen.py       # Session lock screen
│   │   │   ├── dashboard_page.py    # Analytics dashboard
│   │   │   ├── record_list.py       # Record browser with search
│   │   │   ├── record_form.py       # Add/edit record form
│   │   │   ├── profile_view.py      # Full record profile viewer
│   │   │   ├── notification_page.py # Alert management
│   │   │   └── settings_page.py     # Preferences UI
│   │   ├── components/
│   │   │   ├── sidebar.py           # Navigation sidebar
│   │   │   ├── search_bar.py        # Debounced search widget
│   │   │   ├── preview_panel.py     # Quick-view side panel
│   │   │   ├── profile_pic.py       # Profile picture widget
│   │   │   └── audit_viewer_dialog.py  # Audit log dialog
│   │   └── models/                  # Qt table/list models
│   └── utils/
│       ├── paths.py                 # PyInstaller-safe path resolution
│       ├── logger.py                # Rotating file + console logging
│       └── validators.py            # File type & input validators
├── core/
│   └── audit_logger.py              # Audit trail writer
├── styles/
│   └── global.qss                   # Qt stylesheet (dark theme)
├── assets/
│   └── icons/                       # UI icons (arrows, etc.)
├── data/                            # Created at runtime
│   ├── walkin_records.db            # SQLite database
│   ├── documents/                   # Uploaded document files
│   ├── profile_pictures/            # Profile photo storage
│   ├── logs/                        # Application logs
│   └── drafts/                      # Unsaved form drafts
└── scripts/                         # Utility scripts
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **pip** (Python package manager)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd walkin-records

# Install dependencies
pip install PySide6 openpyxl

# Run the application
py main.py
```

On first launch, the system will:
1. Create the `data/` directory and all subdirectories
2. Initialize the SQLite database with all required tables
3. Prompt you to create your admin credentials

### Default Login
On first run, you will be asked to set up a username and password. There is no default — you create it yourself.

---

## 📦 Building an Executable

The project includes a PyInstaller spec file for building a standalone `.exe`:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the application
pyinstaller archivium.spec
```

The output will be at `dist/Archivium/Archivium.exe`. Copy the `data/` folder next to the executable if you want to preserve existing records.

---

## 🗄 Database Schema

| Table | Purpose |
|---|---|
| `walkin_records` | Core student/walk-in information (25+ fields) |
| `documents` | File attachments linked to records |
| `profile_pictures` | One profile photo per record |
| `notifications` | System alerts with severity & lifecycle |
| `auth` | Single-row credentials table |
| `preferences` | Key-value user settings |
| `recent_activity` | View/edit activity log |
| `audit_logs` | Complete action history |

---

## 🔧 Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| UI Framework | PySide6 (Qt6) |
| Database | SQLite3 (WAL mode) |
| Export | openpyxl |
| Logging | Python `logging` with rotation |
| Packaging | PyInstaller |

---

## 📄 License

This project is proprietary and confidential. Unauthorized distribution is prohibited.

---

*Built with ❤️ for walk-in records management.*
