# شغّل التطبيق
run:
	python -m app.main

# أنشئ ملف ترحيل جديد باستخدام Alembic
migrate:
	@if [ -z "$(msg)" ]; then \
		echo "❌ رجاءً استخدم: make migrate msg='اسم التعديل'"; \
		exit 1; \
	fi
	alembic revision --autogenerate -m "$(msg)"

# طبق آخر ترحيل
migration:
	alembic upgrade head

# ثبّت المتطلبات
install:
	pip install -r requirements.txt
