# Heroku Deployment

## Required config vars
- `DATABASE_URL` from Heroku Postgres
- `JWT_SECRET_KEY`
- `DB_REDIS_URI`
- `EASYKASH_PRIVATE_KEY`
- `EASYKASH_SECRET_KEY`
- `ADMIN_NAME`
- `ADMIN_EMAIL`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_LEVEL`
- `CURRENCY_API_KEY`
- `SMTP_STATUS`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_FROM_NAME`

## Notes
- Heroku uses `DATABASE_URL` automatically.
- The app now logs to stdout on Heroku.
- Set `SMTP_STATUS=off` if SMTP is unavailable.
