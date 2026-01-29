#!/bin/bash

# Squad Talk - Quick Setup Script
# هذا السكريبت يسهل عليك تشغيل التطبيق

echo "================================================"
echo "🚀 Squad Talk - Quick Setup"
echo "================================================"
echo ""

# التحقق من وجود Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker غير مثبت!"
    echo "هل تريد تثبيت Docker الآن؟ (y/n)"
    read -r install_docker
    
    if [ "$install_docker" = "y" ]; then
        echo "⏳ جاري تثبيت Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo apt install docker-compose -y
        sudo usermod -aG docker $USER
        echo "✅ تم تثبيت Docker بنجاح!"
        echo "⚠️  يرجى تسجيل الخروج والدخول مرة أخرى لتطبيق التغييرات"
        exit 0
    else
        echo "❌ يجب تثبيت Docker للمتابعة"
        exit 1
    fi
fi

# إنشاء المجلدات المطلوبة
echo "📁 إنشاء المجلدات..."
mkdir -p data ssl

# التحقق من وجود الملفات المطلوبة
if [ ! -f "app.py" ]; then
    echo "❌ ملف app.py غير موجود!"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ ملف requirements.txt غير موجود!"
    exit 1
fi

# سؤال المستخدم عن طريقة التشغيل
echo ""
echo "اختر طريقة التشغيل:"
echo "1) Docker (موصى به)"
echo "2) Python مباشر"
read -p "اختيارك (1 أو 2): " choice

case $choice in
    1)
        echo ""
        echo "🐳 تشغيل باستخدام Docker..."
        
        # بناء وتشغيل الكونتينرز
        if [ -f "docker-compose.yml" ]; then
            docker-compose up -d --build
            
            echo ""
            echo "✅ التطبيق يعمل الآن!"
            echo "🌐 افتح المتصفح على: http://localhost:5000"
            echo ""
            echo "للإيقاف: docker-compose down"
            echo "لمشاهدة اللوقز: docker-compose logs -f"
        else
            echo "❌ ملف docker-compose.yml غير موجود!"
            exit 1
        fi
        ;;
    
    2)
        echo ""
        echo "🐍 تشغيل باستخدام Python..."
        
        # التحقق من Python
        if ! command -v python3 &> /dev/null; then
            echo "❌ Python3 غير مثبت!"
            sudo apt update
            sudo apt install python3 python3-pip python3-venv -y
        fi
        
        # إنشاء virtual environment
        if [ ! -d "venv" ]; then
            echo "⏳ إنشاء virtual environment..."
            python3 -m venv venv
        fi
        
        # تفعيل البيئة وتثبيت المكتبات
        source venv/bin/activate
        echo "⏳ تثبيت المكتبات..."
        pip install -r requirements.txt
        
        # تشغيل التطبيق
        echo ""
        echo "✅ جاري تشغيل التطبيق..."
        echo "🌐 افتح المتصفح على: http://localhost:5000"
        echo ""
        echo "⚠️  اضغط Ctrl+C للإيقاف"
        python3 app.py
        ;;
    
    *)
        echo "❌ اختيار غير صحيح!"
        exit 1
        ;;
esac
