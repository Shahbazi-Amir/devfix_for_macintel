# راهنمای استفاده از DevFix روی Mac Intel

این فایل برای استفاده‌ی روزمره از DevFix ساخته شده تا لازم نباشد هر بار روش صحیح استفاده را به خاطر بیاوری.

## وضعیت فعلی سیستم

در زمان تهیه‌ی این راهنما:

```text
Mac: Intel x86_64
macOS: Monterey 12.7.6
DevFix: 2.0.4
Homebrew: 6.0.13
Homebrew Portable Ruby: 4.0.6
GitHub CLI (gh): 2.97.0 — نصب مستقیم در /usr/local/bin/gh
FFmpeg: 9.0.1-tessus — نصب مستقیم در /usr/local/bin/ffmpeg
FFprobe: 9.0.1-tessus — نصب مستقیم در /usr/local/bin/ffprobe
```

`gh` به GitHub لاگین شده و Credential آن در Keychain مک ذخیره شده است.

FFmpeg و FFprobe هم با تست واقعی encode/probe تأیید شده‌اند.

---

# DevFix دقیقاً چیست؟

DevFix یک VPN سراسری برای کل مک نیست.

DevFix برای ترافیک ابزارهای توسعه ساخته شده است، مثل:

```text
Homebrew
Git
curl
GitHub CLI
npm
Ruby installers
و هر CLI دیگری که با devfix run اجرا شود
```

DevFix در صورت نیاز Tor + Snowflake را بالا می‌آورد و یک مسیر SOCKS محلی ایجاد می‌کند.

## DevFix چه کاری نمی‌کند؟

به‌صورت خودکار این‌ها را از تونل عبور نمی‌دهد:

```text
Safari
Chrome
Firefox
تمام برنامه‌های مک
تمام ترافیک سیستم
```

یعنی روشن بودن DevFix به معنی «VPN کل سیستم» نیست.

---

# قانون ساده‌ی روزمره

## اگر اینترنت مستقیم کار می‌کند

هیچ کاری لازم نیست.

مثلاً:

```bash
gh auth status
git pull
curl https://github.com
```

را می‌توان اول مستقیم امتحان کرد.

## اگر Homebrew، GitHub، GHCR یا دانلود Developer گیر کرد

DevFix را وصل کن:

```bash
devfix connect snowflake
```

صبر کن تا دقیقاً این پیام را ببینی:

```text
Connected with built-in Snowflake.
```

و Shell Prompt دوباره برگردد.

بعد دستور موردنظر را از طریق DevFix اجرا کن.

---

# اتصال و قطع اتصال

## اتصال

```bash
devfix connect snowflake
```

## وضعیت

```bash
devfix status
```

## قطع اتصال

```bash
devfix disconnect
```

## ری‌استارت مسیر

```bash
devfix restart
```

---

# مهم: چه زمانی DevFix را روشن کنم؟

DevFix را وقتی روشن کن که یکی از این موارد رخ دهد:

```text
timeout
TLS failure
connection reset
blocked/unreachable developer endpoint
GHCR مشکل دارد
Homebrew download گیر می‌کند
GitHub download مستقیم پایدار نیست
```

DevFix را لازم نیست همیشه روشن نگه داری.

اگر ابزار مستقیم کار می‌کند، Direct معمولاً سریع‌تر است.

---

# Homebrew

برای Homebrew روی این مک ترجیحاً همیشه از Wrapper خود DevFix استفاده کن:

```bash
devfix brew update
devfix brew outdated
devfix brew install <formula>
devfix brew cleanup
devfix brew doctor
```

## Update با Upgrade فرق دارد

برای تازه کردن اطلاعات Homebrew:

```bash
devfix brew update
```

برای دیدن پکیج‌های قدیمی:

```bash
devfix brew outdated
```

فقط اگر `outdated` چیزی نشان داد، درباره‌ی upgrade تصمیم بگیر:

```bash
devfix brew upgrade
```

اگر `outdated` خالی است، `upgrade` کلی لازم نیست.

---

# هشدار macOS 12 / Tier 3

Homebrew روی Monterey ممکن است این هشدار را بدهد:

```text
Warning: You are using macOS 12.
This is a Tier 3 configuration.
```

این هشدار به‌تنهایی به معنی خرابی Homebrew نیست.

بعضی Formulaهای جدید روی Intel Monterey Bottle آماده ندارند و ممکن است مجبور به build from source شوند.

بنابراین هر خطای install لزوماً مشکل DevFix یا اینترنت نیست.

---

# GitHub CLI — gh

`gh` الان مستقیم در این مسیر نصب شده:

```text
/usr/local/bin/gh
```

بررسی نسخه:

```bash
gh --version
```

بررسی Login:

```bash
gh auth status
```

Login در Keychain ذخیره می‌شود.

## مهم

خاموش کردن DevFix باعث Logout شدن `gh` نمی‌شود.

این دو مستقل‌اند:

```text
gh login = هویت و Credential GitHub
DevFix   = مسیر شبکه
```

اگر `gh` مستقیم کار می‌کند، لازم نیست DevFix روشن باشد.

اگر شبکه GitHub مشکل داشت:

```bash
devfix run gh <command>
```

مثلاً:

```bash
devfix run gh auth status
```

---

# Git

اگر Git مستقیم کار می‌کند:

```bash
git pull
git push
```

اگر مسیر شبکه مشکل داشت:

```bash
devfix git pull
devfix git push
devfix git clone https://github.com/OWNER/REPO.git
```

---

# curl و دانلود فایل

اگر URL مستقیم قابل دسترس است:

```bash
curl -fL -O <URL>
```

اگر مسیر مستقیم مشکل دارد:

```bash
devfix curl -fL -O <URL>
```

برای اتصال‌های ناپایدار می‌توان از Retry استفاده کرد:

```bash
devfix curl --http1.1 -fL \
  --retry 10 \
  --retry-all-errors \
  --retry-delay 3 \
  -O <URL>
```

اگر فایل کوچک با Snowflake چند ساعت ETA نشان می‌دهد، منتظر نمان.
در صورت امکان Direct را امتحان کن.

---

# اجرای هر CLI از مسیر DevFix

قالب عمومی:

```bash
devfix run <command> [args...]
```

مثال:

```bash
devfix run npm install
devfix run python script.py
devfix run gh repo view
```

این برای برنامه‌های Command-Line است.

---

# آیا DevFix می‌تواند سایت یا IP فیلترشده را باز کند؟

## برای CLI: بله، در حد یک درخواست شبکه

مثلاً:

```bash
devfix curl https://example.com
```

یا:

```bash
devfix curl https://1.2.3.4
```

اگر مقصد از طریق Tor/Snowflake قابل دسترس باشد، درخواست می‌تواند از آن مسیر عبور کند.

## برای مرورگر: نه به‌صورت خودکار

DevFix در نسخه فعلی یک VPN سراسری یا Browser VPN نیست.

این دستور وجود ندارد:

```text
devfix open <blocked-site>
```

و DevFix خودش Safari/Chrome را به‌طور خودکار Proxy نمی‌کند.

DevFix یک SOCKS محلی برای Processهای مدیریت‌شده‌ی خودش می‌سازد، نه تنظیم سراسری Network macOS.

پس برای وب‌گردی عمومی از DevFix به‌عنوان VPN دائمی استفاده نکن.

---

# External Proxy

اگر روزی یک Proxy خارجی معتبر داشتی، DevFix می‌تواند آن را هم استفاده کند:

```bash
devfix proxy set socks5h://127.0.0.1:1080
devfix connect external-proxy
```

و برای دیدن وضعیت:

```bash
devfix proxy status
```

پاک کردن:

```bash
devfix proxy clear
```

این بخش برای Proxy موجود است؛ DevFix خودش IP Proxy دلخواه تولید نمی‌کند.

---

# Transportها

دیدن Transportها:

```bash
devfix transport list
```

وضعیت:

```bash
devfix transport status
```

تست Direct:

```bash
devfix transport test direct
```

تست Snowflake:

```bash
devfix transport test snowflake
```

انتخاب خودکار:

```bash
devfix transport auto
```

---

# اگر Snowflake گیر کرد

اگر زیر 100٪ متوقف شد:

```text
Bootstrap / Transport failure
```

اگر به 100٪ رسید ولی Endpoint validation شکست خورد:

```text
Route validation failure
```

این دو مشکل متفاوت‌اند.

یک Session خراب Snowflake لزوماً به معنی خرابی DevFix نیست.

ابتدا:

```bash
devfix disconnect
devfix connect snowflake
```

یک بار با اینترنت پایدار امتحان کن.

شبکه، Wi‑Fi یا Hotspot را وسط Bootstrap یا Download عوض نکن.

---

# Log و عیب‌یابی

آخرین Logها:

```bash
devfix logs --tail 200
```

Doctor:

```bash
devfix doctor
```

Doctor کامل‌تر:

```bash
devfix doctor --verbose
```

قبل از فرستادن Log در جای عمومی، آن را مرور کن.

---

# FFmpeg و FFprobe

این دو در حال حاضر مستقیم نصب شده‌اند، نه توسط Homebrew.

مسیرها:

```text
/usr/local/bin/ffmpeg
/usr/local/bin/ffprobe
```

بررسی:

```bash
ffmpeg -version
ffprobe -version
```

بنابراین:

```bash
brew upgrade
```

آن‌ها را آپدیت نمی‌کند.

برای آپدیت آینده باید نسخه‌ی جدید Direct به‌صورت جدا بررسی و نصب شود.

---

# gh هم Homebrew-managed نیست

`gh` نیز در حال حاضر Direct install است:

```text
/usr/local/bin/gh
```

پس Homebrew آن را آپدیت نمی‌کند.

قبل از نصب دوباره‌ی:

```bash
brew install gh
brew install ffmpeg
```

حتماً بررسی کن که Direct install فعلی با Homebrew conflict نکند.

---

# دستورات سریع موردنیاز

## روشن کردن DevFix

```bash
devfix connect snowflake
```

## وضعیت

```bash
devfix status
```

## Homebrew

```bash
devfix brew update
devfix brew outdated
```

## GitHub CLI

```bash
gh auth status
```

## Git از مسیر DevFix

```bash
devfix git <args>
```

## curl از مسیر DevFix

```bash
devfix curl <args>
```

## هر CLI

```bash
devfix run <command> <args>
```

## خاموش کردن

```bash
devfix disconnect
```

---

# چیزهایی که نباید بی‌دلیل انجام بدهی

بدون دلیل مشخص این کارها را انجام نده:

```text
brew reinstall ...
brew upgrade وقتی outdated خالی است
حذف Homebrew
حذف Portable Ruby
disable SIP
disable Gatekeeper
curl -k به‌عنوان راه دائمی
chmod 777
پاک کردن tor-data بدون backup
نصب دوباره gh/ffmpeg از Homebrew روی Direct install موجود
```

---

# مدل ذهنی خیلی ساده

```text
GitHub Login
    |
    +-- gh Credential در Keychain
    |   ماندگار است و با disconnect شدن DevFix از بین نمی‌رود
    |
    +-- DevFix
        فقط مسیر شبکه است
        فقط وقتی نیاز است روشنش کن
```

و:

```text
Direct کار می‌کند؟
    |
    +-- بله → Direct استفاده کن
    |
    +-- نه → devfix connect snowflake
             سپس devfix brew / git / curl / run
             و بعد از پایان کار devfix disconnect
```

---

# قانون نهایی

DevFix را به‌عنوان «ابزار شبکه برای Developer CLIها» در نظر بگیر، نه VPN دائمی کل مک.

اگر مستقیم کار می‌کند، مستقیم برو.

اگر Developer endpoint مسدود/ناپایدار است، Snowflake را روشن کن.

اگر Homebrew خطا داد، اول مشخص کن مشکل Network است یا Compatibility/Formula؛ کورکورانه reinstall یا upgrade نکن.
