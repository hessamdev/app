import os
from github import Github

# خواندن توکن از محیط
github_token = os.getenv("GITHUB_TOKEN")

# اتصال به گیت‌هاب با استفاده از توکن
g = Github(github_token)

# انتخاب مخزن
repo = g.get_repo("hessamdev/app")

# دریافت لیست فایل‌ها و محتویات
contents = repo.get_contents("")
for content_file in contents:
    print(content_file.name)
