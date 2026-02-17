# استخدام نسخة بايثون خفيفة وقوية
FROM python:3.11-slim-bookworm

# 1. إعدادات النظام الأساسية
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/app

WORKDIR /app

# 2. تثبيت أدوات النظام (نحتاجها لاحقاً للمهارات)
RUN apt-get update && apt-get install -y \
    curl git build-essential supervisor \
    && rm -rf /var/lib/apt/lists/*

# 3. إنشاء مستخدم غير الـ Root (للأمان)
RUN useradd -m -u 1000 user
RUN chown -R user:user /app

# 4. تثبيت المكتبات
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 5. نسخ ملفات المشروع
COPY --chown=user:user . .

# 6. إعداد المجلدات الخاصة بالبيانات
RUN mkdir -p /app/data /app/logs && \
    chown -R user:user /app/data /app/logs

# 7. التبديل للمستخدم
USER user

# 8. المنافذ
EXPOSE 7860

# 9. نقطة الانطلاق (Supervisord)
CMD ["supervisord", "-c", "supervisord.conf"]
