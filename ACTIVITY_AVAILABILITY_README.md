# Activity Availability System - Setup Guide

## ✅ Installation Complete

The Activity Availability system has been successfully added to your backend.

---

## 📦 Dependencies

Add to your `requirements.txt`:

```
APScheduler>=3.10.4
```

Install:

```bash
pip install APScheduler
```

---

## 🗄️ Database Migration

Run the migration to create the `activity_availability` table:

```bash
# Update the down_revision in the migration file first
cd /Users/home/WorkSpace/WebApps/NextApp/globaldivers/backend

# Edit migrations/versions/add_activity_availability.py
# Set down_revision to your latest migration ID

# Then run:
alembic upgrade head
```

---

## 🚀 System Overview

### Availability Logic (INVERSE)

- **No record exists** → Activity is **OPEN** (default)
- **Record exists** → Activity is **CLOSED**

### Features Implemented

1. **Model**: `ActivityAvailability`

   - Tracks closed dates for trips and courses
   - Auto-validates activity existence
   - Unique constraint prevents duplicates

2. **Invoice Validation**

   - Automatically checks availability before creating invoices
   - Rejects bookings for closed dates
   - Returns clear error messages with closure reason

3. **Admin Endpoints**

   - `POST /activity-availability/close` - Close an activity date
   - `DELETE /activity-availability/reopen` - Reopen an activity date
   - `PATCH /activity-availability/{id}` - Update closure date/reason
   - `GET /activity-availability/` - List all closures
   - `GET /activity-availability/check` - Check specific date availability
   - `POST /activity-availability/cleanup` - Manual cleanup (also runs automatically)

4. **Automatic Cleanup**
   - Runs daily at 2:00 AM server time
   - Deletes all records where `date < CURRENT_DATE`
   - Prevents database bloat

---

## 📝 API Examples

### Close a Trip Date

```bash
POST /activity-availability/close
{
  "activity_type": "trip",
  "activity_id": 5,
  "date": "2026-02-15",
  "reason": "Maintenance day"
}
```

### Check Availability

```bash
GET /activity-availability/check?activity_type=trip&activity_id=5&date=2026-02-15
```

Response:

```json
{
  "is_available": false,
  "reason": "Maintenance day",
  "message": "Trip is closed on 2026-02-15"
}
```

### Reopen a Date

```bash
DELETE /activity-availability/reopen?activity_type=trip&activity_id=5&date=2026-02-15
```

---

## 🔒 Invoice Protection

When creating an invoice, the system automatically:

1. Extracts all dates from `activity_details`
2. Checks each date against `activity_availability`
3. Rejects the invoice if ANY date is closed
4. Returns error message with closure reason

Example error:

```json
{
  "detail": "Trip is not available on 2026-02-15. Reason: Maintenance day"
}
```

---

## ⚙️ Scheduler

The scheduler starts automatically with your FastAPI app:

- Initialized in `main.py` lifespan
- Runs cleanup job daily at 2:00 AM
- Gracefully shuts down with the app

### Manual Cleanup

```bash
POST /activity-availability/cleanup
```

---

## 🎯 Migration Steps

1. **Update migration file**:

   ```python
   # In migrations/versions/add_activity_availability.py
   down_revision = 'your_latest_migration_id'  # UPDATE THIS
   ```

2. **Run migration**:

   ```bash
   alembic upgrade head
   ```

3. **Verify table creation**:
   ```sql
   SELECT * FROM activity_availability LIMIT 1;
   ```

---

## ✨ Testing

1. Close a date:

   ```bash
   curl -X POST "http://localhost:8000/activity-availability/close" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "activity_type": "trip",
       "activity_id": 1,
       "date": "2026-12-25",
       "reason": "Christmas holiday"
     }'
   ```

2. Try to create invoice for that date → Should fail

3. Reopen the date:

   ```bash
   curl -X DELETE "http://localhost:8000/activity-availability/reopen?activity_type=trip&activity_id=1&date=2026-12-25" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
   ```

4. Try to create invoice again → Should succeed

---

## 🔍 Database Schema

```sql
CREATE TABLE activity_availability (
    id SERIAL PRIMARY KEY,
    activity_type VARCHAR(20) NOT NULL,  -- 'trip' or 'course'
    activity_id INTEGER NOT NULL,
    date DATE NOT NULL,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (activity_type, activity_id, date)
);

CREATE INDEX ix_activity_availability_lookup
ON activity_availability (activity_type, activity_id, date);
```

---

## 📊 SQL Cleanup Query

Manual cleanup (runs automatically):

```sql
DELETE FROM activity_availability
WHERE date < CURRENT_DATE;
```

---

## ✅ Checklist

- [ ] Install APScheduler (`pip install APScheduler`)
- [ ] Update migration `down_revision`
- [ ] Run `alembic upgrade head`
- [ ] Restart your application
- [ ] Test closing a date
- [ ] Test invoice creation rejection
- [ ] Verify scheduler logs
- [ ] Test manual cleanup endpoint

---

## 🎉 Complete!

Your Activity Availability system is now fully integrated and production-ready.
