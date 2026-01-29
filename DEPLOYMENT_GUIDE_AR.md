# 🚀 دليل نشر Squad Talk على السيرفر

## 📋 المتطلبات

### قبل البدء، تحتاج:
- سيرفر لينكس (Ubuntu 20.04+ مفضل)
- Docker و Docker Compose مثبتين
- دومين (اختياري لكن موصى به)
- حساب Gmail لإرسال الإيميلات

---

## 🎯 خيارات النشر السهلة

### الطريقة 1️⃣: النشر باستخدام Docker (الأسهل والأسرع)

#### الخطوة 1: تثبيت Docker
```bash
# تحديث النظام
sudo apt update && sudo apt upgrade -y

# تثبيت Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# تثبيت Docker Compose
sudo apt install docker-compose -y

# إضافة المستخدم الحالي لمجموعة Docker
sudo usermod -aG docker $USER
newgrp docker
```

#### الخطوة 2: تحضير الملفات
```bash
# إنشاء مجلد للمشروع
mkdir -p ~/squadtalk
cd ~/squadtalk

# نسخ الملفات التالية للمجلد:
# - app.py
# - requirements.txt
# - wsgi.py
# - Dockerfile
# - docker-compose.yml
# - nginx.conf

# إنشاء مجلد للداتا
mkdir -p data
```

#### الخطوة 3: تعديل إعدادات الإيميل
افتح ملف `app.py` وعدل السطور التالية (حوالي السطر 25-30):

```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'بريدك@gmail.com',  # غير هذا
    'sender_password': 'كلمة-سر-التطبيق'   # غير هذا
}
```

**مهم**: استخدم "App Password" من Gmail، مش كلمة سر حسابك العادية!

كيف تحصل على App Password:
1. اذهب لإعدادات Google Account
2. Security → 2-Step Verification (لازم يكون مفعل)
3. App passwords → أنشئ كلمة سر جديدة للتطبيق

#### الخطوة 4: تشغيل التطبيق
```bash
# بناء وتشغيل الكونتينرز
docker-compose up -d --build

# شوف اللوقز للتأكد إن كل شيء يشتغل
docker-compose logs -f
```

#### الخطوة 5: الوصول للتطبيق
افتح المتصفح وروح لـ:
- `http://localhost:5000` (إذا على نفس السيرفر)
- `http://IP-السيرفر:5000` (من جهاز ثاني)

---

### الطريقة 2️⃣: النشر بدون Docker (تثبيت مباشر)

#### الخطوة 1: تثبيت Python والمتطلبات
```bash
# تحديث النظام
sudo apt update && sudo apt upgrade -y

# تثبيت Python و pip
sudo apt install python3 python3-pip python3-venv -y

# إنشاء مجلد للمشروع
mkdir -p ~/squadtalk
cd ~/squadtalk
```

#### الخطوة 2: إنشاء Virtual Environment
```bash
# إنشاء البيئة الافتراضية
python3 -m venv venv

# تفعيل البيئة
source venv/bin/activate

# تثبيت المكتبات
pip install -r requirements.txt
```

#### الخطوة 3: تعديل ملف app.py
نفس خطوة تعديل الإيميل من الطريقة الأولى.

#### الخطوة 4: تشغيل التطبيق
```bash
# تشغيل مباشر (للتجربة)
python3 app.py

# أو للتشغيل في الخلفية
nohup python3 app.py > squadtalk.log 2>&1 &
```

#### الخطوة 5: جعل التطبيق يعمل تلقائياً (systemd service)
أنشئ ملف `/etc/systemd/system/squadtalk.service`:

```bash
sudo nano /etc/systemd/system/squadtalk.service
```

محتوى الملف:
```ini
[Unit]
Description=Squad Talk Application
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/squadtalk
Environment="PATH=/home/your-username/squadtalk/venv/bin"
ExecStart=/home/your-username/squadtalk/venv/bin/python wsgi.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

غير `your-username` باسم المستخدم الحقيقي.

```bash
# تفعيل وتشغيل الخدمة
sudo systemctl daemon-reload
sudo systemctl enable squadtalk
sudo systemctl start squadtalk

# شوف الحالة
sudo systemctl status squadtalk
```

---

## 🌐 إعداد الدومين (اختياري لكن موصى به)

### إذا عندك دومين:

#### الخطوة 1: ربط الدومين بالسيرفر
في لوحة تحكم الدومين، أضف DNS Record:
```
Type: A
Name: @ (أو subdomain مثل chat)
Value: IP السيرفر
TTL: 3600
```

#### الخطوة 2: تثبيت Nginx
```bash
sudo apt install nginx -y
```

#### الخطوة 3: إعداد Nginx
أنشئ ملف كونفق:
```bash
sudo nano /etc/nginx/sites-available/squadtalk
```

محتوى الملف (بدون SSL):
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
    }

    location /socket.io {
        proxy_pass http://localhost:5000/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_buffering off;
    }
}
```

```bash
# تفعيل الكونفق
sudo ln -s /etc/nginx/sites-available/squadtalk /etc/nginx/sites-enabled/

# تجربة الكونفق
sudo nginx -t

# إعادة تشغيل Nginx
sudo systemctl restart nginx
```

#### الخطوة 4: إضافة SSL (مجاني من Let's Encrypt)
```bash
# تثبيت Certbot
sudo apt install certbot python3-certbot-nginx -y

# الحصول على شهادة SSL
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# التجديد التلقائي مفعل بشكل افتراضي
# تأكد منه بـ:
sudo certbot renew --dry-run
```

---

## 🔥 نشر سريع على منصات الاستضافة الشهيرة

### على Railway.app (مجاني للبداية)
1. سجل في https://railway.app
2. New Project → Deploy from GitHub
3. اربط الريبو
4. Railway بيكتشف Flask تلقائياً
5. أضف المتغيرات البيئية في Settings

### على Render.com (مجاني للبداية)
1. سجل في https://render.com
2. New Web Service
3. اربط GitHub repo
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python wsgi.py`
6. أضف Environment Variables

### على DigitalOcean App Platform
1. سجل في DigitalOcean
2. Create App → من GitHub
3. اختر الريبو
4. حدد Python
5. Run Command: `python wsgi.py`

### على Heroku
1. تثبيت Heroku CLI
2. إنشاء ملف `Procfile`:
```
web: python wsgi.py
```
3. الأوامر:
```bash
heroku login
heroku create squadtalk-app
git push heroku main
heroku open
```

---

## 🔧 أوامر مفيدة للإدارة

### Docker Commands:
```bash
# شوف الكونتينرز الشغالة
docker-compose ps

# أوقف التطبيق
docker-compose down

# شغل التطبيق
docker-compose up -d

# شوف اللوقز
docker-compose logs -f

# أعد بناء الكونتينر بعد تعديل الكود
docker-compose up -d --build

# دخول للكونتينر
docker exec -it squadtalk-app bash
```

### Systemd Commands (بدون Docker):
```bash
# ابدأ الخدمة
sudo systemctl start squadtalk

# أوقف الخدمة
sudo systemctl stop squadtalk

# أعد تشغيل الخدمة
sudo systemctl restart squadtalk

# شوف الحالة
sudo systemctl status squadtalk

# شوف اللوقز
journalctl -u squadtalk -f
```

---

## 🛡️ نصائح الأمان

1. **غير كلمة السر السرية**:
   في app.py، غير `app.secret_key`

2. **استخدم HTTPS**:
   ما تشغل التطبيق على الإنترنت بدون SSL

3. **حدد معدل الطلبات**:
   أضف rate limiting لحماية من الـ abuse

4. **Firewall**:
```bash
# فتح البورتات المطلوبة فقط
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

5. **تحديثات دورية**:
```bash
sudo apt update && sudo apt upgrade -y
```

---

## 🐛 حل المشاكل الشائعة

### التطبيق ما يشتغل:
```bash
# شوف اللوقز
docker-compose logs -f
# أو
journalctl -u squadtalk -f
```

### مشاكل البورت:
```bash
# شوف إيش يستخدم البورت 5000
sudo lsof -i :5000

# أوقف العملية إذا لزم
sudo kill -9 PID
```

### WebSocket ما يتصل:
- تأكد من إعدادات Nginx صحيحة
- تأكد من Firewall ما يحجب الاتصال

### الإيميلات ما ترسل:
- تأكد من App Password صحيح
- تأكد من "Less secure apps" مفعل (أو استخدم App Password)
- جرب من terminal:
```bash
python3 -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587)"
```

---

## 📊 مراقبة الأداء

### شوف استخدام الموارد:
```bash
# Docker stats
docker stats

# System resources
htop
```

### Monitoring with Prometheus (متقدم):
يمكنك تركيب Prometheus و Grafana للمراقبة الاحترافية.

---

## 📞 الدعم

إذا واجهتك أي مشكلة:
1. شوف اللوقز أولاً
2. تأكد من جميع المتغيرات مضبوطة صح
3. جرب على localhost أولاً قبل النشر

---

## ✅ Checklist قبل النشر

- [ ] عدلت إعدادات الإيميل في app.py
- [ ] اختبرت التطبيق على localhost
- [ ] غيرت secret_key
- [ ] ربطت الدومين (إذا عندك)
- [ ] نصبت SSL certificate
- [ ] ضبطت Firewall
- [ ] اختبرت Socket.IO connection
- [ ] اختبرت إرسال الإيميلات
- [ ] عملت backup للبيانات

---

## 🎉 تهانينا!

تطبيقك الآن على الإنترنت! شاركه مع أصدقائك واستمتعوا بالدردشة الصوتية والنصية.

**رابط التطبيق**: http://your-domain.com (أو http://your-server-ip:5000)

---

## 📝 ملاحظات إضافية

### تحسينات مستقبلية موصى بها:
1. إضافة قاعدة بيانات حقيقية (PostgreSQL أو MySQL)
2. تخزين الملفات في S3 أو مكان آمن
3. إضافة Redis للـ caching
4. إضافة CDN للأصول الثابتة
5. Horizontal scaling مع Load Balancer

### الباقات المجانية للبداية:
- **Railway**: 500 ساعة/شهر مجاناً
- **Render**: مجاني للمشاريع الصغيرة
- **Fly.io**: مجاني للتطبيقات الصغيرة
- **Heroku**: (dyno مجاني لكن محدود)

حظ موفق! 🚀
