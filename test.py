import requests

# 🔑 مفتاح Firebase الخاص بـ fitroom.app
FIREBASE_API_KEY = "AIzaSyBEIsqlZ5eFfCvjNTKRCpa2iddE2t24mDY"

# 📧 بريد المستخدم
email = "yousseifmuhammed@gmail.com"

# 1️⃣ إرسال رابط تسجيل الدخول إلى الإيميل
send_link_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
payload = {
    "requestType": "EMAIL_SIGNIN",
    "email": email,
    "continueUrl": "https://fitroom.app"
}

resp = requests.post(send_link_url, json=payload)
if resp.status_code == 200:
    print("✅ تم إرسال رابط تسجيل الدخول إلى الإيميل.")
else:
    print("❌ فشل في إرسال الرابط:", resp.text)
    exit()

# 2️⃣ انتظار المستخدم لفتح الإيميل ولصق الرابط هنا
link = input("📥 الصق هنا رابط تسجيل الدخول الذي وصلك على الإيميل:\n")

# 3️⃣ تسجيل الدخول باستخدام الرابط
signin_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithEmailLink?key={FIREBASE_API_KEY}"
signin_payload = {
    "email": email,
    "oobCode": link.split("oobCode=")[1].split("&")[0]
}

signin_resp = requests.post(signin_url, json=signin_payload)

if signin_resp.status_code == 200:
    id_token = signin_resp.json()["idToken"]
    print("\n✅ تم تسجيل الدخول بنجاح!")
    print("🪪 ID Token:", id_token)
else:
    print("❌ فشل في تسجيل الدخول:", signin_resp.text)
