# IIA Vendor Bill & Inventory Management System

Enterprise-style Flask application for **Indian Institute of Astrophysics (IIA) — Vainu Bappu Observatory, Kavalur** covering vendor master data, vendor bills with line items, **stock lots linked to bill lines**, employee master, item issues/returns, RBAC, audit logging, dashboard, and Excel/PDF exports.

## Stack

- Flask 3, Blueprints, SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate  
- **SQLite** by default (`<project>/instance/iia_vbo.sqlite`). Override with `DATABASE_URL` if you later use PostgreSQL/MySQL.  
- Bootstrap 5 UI, Chart.js dashboard  
- Pandas + OpenPyXL (Excel), ReportLab (PDF)

## Quick start

1. **Python environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuration**

   ```bash
   cp .env.example .env
   # Edit SECRET_KEY. DATABASE_URL is optional (defaults to SQLite under instance/).
   ```

3. **Database schema**

   On first run in **development** (`FLASK_ENV` not `production`), the app calls `db.create_all()` and seeds roles + **`admin` / `admin123`** if the DB is empty — no manual step required for a quick start.

   For controlled schema history, prefer Flask-Migrate:

   ```bash
   export FLASK_APP=run.py
   flask db init          # first time only
   flask db migrate -m "initial"
   flask db upgrade
   flask seed-db
   ```

   Manual shortcut (no Alembic):

   ```bash
   flask create-all
   flask seed-db
   ```

4. **Run**

   ```bash
   python run.py
   ```

   Default seeded login: **`admin` / `admin123`** — change immediately after first login.

## Architecture

| Area | Path |
|------|------|
| App factory | `app/__init__.py` |
| Models | `app/models/` |
| Blueprints | `app/blueprints/` |
| Services (workflow) | `app/services/` |
| Reports / exports | `app/reports/` |
| Templates | `app/templates/` |
| Static | `app/static/` |

### Stock model

- **`BillLineItem`**: commercial line on a vendor bill (links to `ItemMaster` for stock-backed items).  
- **`StockLot`**: `bill_line_id` + `item_master_id`, `quantity_received`, `quantity_available`. Lots are created when a bill reaches **full approval** (see `stock_lot_service.create_lots_for_bill_lines`).  
- **`IssueLine`**: issues consume `StockLot.quantity_available`; returns restock except **`lost`** (no restoral, audit movement recorded).

## Roles (seeded)

`super_admin`, `admin`, `accounts`, `inventory_manager`, `store_keeper`, `staff_viewer`

Extend behaviour via `app/utils/decorators.py` (`role_required`).

## Dynamic mandatory fields (Admin)

**Super Admin / Admin** can open **Admin → Field rules** and, per module (vendor, bill, bill line, item, category, employee, issue), choose which fields are **mandatory** and which participate in **duplicate detection**. Rules are stored in `form_field_rules` and enforced in WTForms and in the browser (`static/js/form-validation.js`). **Validation logs** (Admin → Validation logs) capture server-side outcomes for debugging.

## Production notes

- Set `FLASK_ENV=production`, strong `SECRET_KEY`, and `SESSION_COOKIE_SECURE=1` behind HTTPS.  
- **SQLite**: back up `instance/iia_vbo.sqlite` (and `instance/uploads/`) on a schedule; for heavy concurrent writes consider PostgreSQL/MySQL via `DATABASE_URL`.  
- Use a real SMTP server for password reset (development shows reset link in a flash message).  
- Prefer `gunicorn wsgi:app` (or similar) and `flask db upgrade` in deploy pipeline.  
- Store uploads only under `instance/uploads` (already configured).

## Licence / affiliation

This repository is a **software template** for observatory operations. Official IIA branding assets should be supplied and approved by the institute before public deployment.
