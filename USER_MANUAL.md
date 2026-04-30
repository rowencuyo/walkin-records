# International Student Services — User Manual

---

## 1. Getting Started

### Logging In
When you open the app, you'll see a **login screen**. Enter your **username** and **password** to sign in.

> **First-time users:** The default credentials are set during initial setup. Contact your administrator if you don't have them.

### Lock Screen
If the app is idle for too long (and auto-lock is enabled), it will lock. Just enter your **password** to unlock — no need to re-enter your username.

---

## 2. Dashboard

The **Dashboard** is the first thing you see after logging in. It gives you a quick overview of everything important:

| Card | What It Shows |
|------|---------------|
| **Active Records** | Total number of active student records |
| **Inactive Records** | Records that have been soft-deleted |
| **Missing Documents** | Students missing required documents |
| **Expired Visas** | Students with expired visas |
| **Expiring Soon** | Visas expiring within the configured threshold (default: 30 days) |
| **Not Updated (90d)** | Records not updated in the last 90 days |

**Click any card** to jump directly to a filtered list of those records.

### Alerts
Shows the top 5 active notifications (visa expiry, missing docs, etc.). Click **"View All"** to go to the Notifications page, or **"Open"** to go directly to a student's profile.

### Record Trends
A line chart showing how many records were created each month over the last 6 months.

### Recent Activity
Shows the last 10 records that were viewed or edited. Click **"View"** to open any of them.

---

## 3. Records

### Viewing Records
You can browse records in two ways — toggle between them using the **Table** and **Cards** buttons:

- **Card View** (default) — Visual cards showing student name, passport, visa info, and a completeness badge
- **Table View** — Spreadsheet-style list with sortable columns

### Searching & Filtering
Use the **Search Bar** at the top to find records by name, passport number, or other details. You can also filter by:
- Visa status
- Educational level
- Year level
- Active / Archived status

### Opening a Record
- **Single click** → Opens a preview panel on the side
- **Double click** → Opens the full profile view

### Adding a New Record
Click the **"+ Add Record"** button to open the record form.

### Batch Status Update (Table View)
1. Hold **Ctrl** or **Shift** and click to select multiple rows
2. A blue toolbar appears at the bottom
3. Choose an enrollment status from the dropdown
4. Click **"Apply"** to update all selected records at once

### Pagination
Navigate between pages using the **Previous / Next** buttons. You can change how many records show per page (25, 50, 100, or 200).

---

## 4. Record Form (Add / Edit)

The form has four sections:

| Section | Key Fields |
|---------|------------|
| **Identity** | Last Name*, First Name*, Sex*, Date of Birth*, Passport Number*, Country* |
| **Philippine Residential Address** | Street, Barangay, City, Province, Region |
| **Academic & Residency** | Arrival date, Education start, Level, Course, Year, Semester, Remarks |
| **Visa Information** | Category, Grant date, Validity date, Status, Comments |

> Fields marked with **\*** are required. The form will highlight errors if you miss any.

### Autosave Drafts
The form **automatically saves a draft every 30 seconds**. If you close the app or navigate away, next time you open the form you'll be asked if you want to **restore** or **discard** the draft.

### Unsaved Changes
If you try to leave the form with unsaved changes, a dialog will ask you to **Save**, **Discard**, or **Cancel**.

---

## 5. Student Profile

After opening a record, you'll see the full student profile with:

- **Profile Picture** — Click to upload or remove a photo (JPG, PNG, or WebP, max 5 MB)
- **Completeness Banner** — Orange banner if any required fields or documents are missing
- **Visa Countdown Badge** — Color-coded indicator:
  - 🟢 **Green** — More than 30 days remaining
  - 🟡 **Amber** — 30 days or less remaining
  - 🔴 **Red** — Already expired

### Documents
- Click **"+ Upload Document"** to add a file (PDF, JPG, PNG, DOC/DOCX, max 25 MB)
- Document types: Passport, Birth Certificate, Graduation Certificate, Good Moral Certificate, Bank Statement
- If a file is missing from disk, a red **"!! MISSING FILE"** warning appears with a **"Locate"** button to re-link it

### Delete / Restore
- **Delete** — Soft-deletes the record (it becomes inactive but can be restored)
- **Restore** — Brings an inactive record back to active status

---

## 6. Notifications

Three tabs:

| Tab | Contents |
|-----|----------|
| **Active** | Unread and read alerts that need attention |
| **Dismissed** | Alerts you've manually dismissed |
| **History** | Resolved alerts (e.g., visas that were renewed) |

- Click **"Dismiss"** to move an alert out of the Active tab
- Click **"Mark All Read"** to mark everything as read
- Click **"Open"** to jump to the related student profile

---

## 7. Settings

### Security
- **Idle Auto-Lock** — Enable/disable and set timeout (5, 10, 15, 30, or 60 minutes)
- **Change Password** — Enter current password, then set a new one (minimum 4 characters)
- **Change Username** — Requires your password for verification

### Notifications
- Toggle **visa expiry**, **missing documents**, and **backup reminder** alerts on/off
- Set the **warning threshold** for visa expiry (7–180 days before expiration)
- Set **notification retention** period (7–365 days)

### Data & Export
- Select a **date range** and click **"Export Records"** to generate an Excel file (.xlsx)

### Backup & Restore
- **Create Backup** — Saves a copy of the entire database and files to a folder you choose
- **Restore** — Replaces ALL current data with a previous backup (⚠️ this is irreversible)

### Audit Log
- Click **"View System Audit Logs"** to see a complete history of all actions (logins, record changes, exports, etc.)

### About
- Shows the app name, version number, and data directory location

---

## Quick Reference

| Action | How To |
|--------|--------|
| Add a student | Records → **+ Add Record** |
| Find a student | Use the **Search Bar** on the Records page |
| Upload a document | Open profile → Documents → **+ Upload Document** |
| Export to Excel | Settings → Data & Export → **Export Records** |
| Back up your data | Settings → Backup & Restore → **Create Backup** |
| Change your password | Settings → Security → **Change Password** |
| Check visa alerts | Dashboard → **Alerts** section, or **Notifications** page |
