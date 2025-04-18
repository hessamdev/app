import requests

# URL API
url = "https://petstore.swagger.io/v2/store/inventory"

# ارسال درخواست GET به API
try:
    # ارسال درخواست به API
    response = requests.get(url)

    # بررسی اینکه آیا پاسخ موفقیت‌آمیز بوده است یا نه
    response.raise_for_status()  # اگر پاسخ خطا بود، استثناء ایجاد می‌شود

    # تجزیه و تحلیل پاسخ JSON
    data = response.json()
    
    print("موجودی فروشگاه:")
    print(data)
    
except requests.exceptions.RequestException as e:
    print(f"خطا در ارسال درخواست: {e}")
