# راهنمای استفاده از DevFix روی Mac Intel

این راهنما برای استفاده‌ی روزمره از DevFix است تا روش صحیح استفاده، اتصال Snowflake، Homebrew، `gh`، Git، `curl` و ابزارهای نصب مستقیم فراموش نشود.

## وضعیت مبنا هنگام تهیه این راهنما

```text
Mac: Intel x86_64
macOS: Monterey 12.7.6
DevFix: 2.0.4
Homebrew: 6.0.13
Homebrew Portable Ruby: 4.0.6
GitHub CLI (gh): 2.97.0 — Direct install
FFmpeg: 9.0.1-tessus — Direct install
FFprobe: 9.0.1-tessus — Direct install
```

`gh` با OAuth به GitHub لاگین شده و Credential آن در Keychain مک ذخیره شده است. FFmpeg/FFprobe با تست واقعی encode/probe تأیید شده‌اند.

---

## DevFix دقیقاً چیست؟

DevFix یک VPN سراسری برای کل مک نیست. DevFix برای ترافیک ابزارهای توسعه ساخته شده است؛ مانند:

```text
Homebrew
Git
curl
GitHub CLI
npm
Ruby installers
هر CLI که با devfix run اجرا شود
```

DevFix در صورت نیاز Tor + Snowflake را بالا می‌آورد و یک مسیر SOCKS محلی ایجاد می‌کند.

به‌صورت خودکار Safari، Chrome، Firefox، تمام برنامه‌های مک یا تمام ترافیک سیستم را از تونل عبور نمی‌دهد.

---

## قانون ساده‌ی روزمره

اگر اینترنت مستقیم کار می‌کند، DevFix لازم نیست. ابتدا ابزار را مستقیم امتحان کن.

اگر Homebrew، GitHub، GHCR یا دانلود Developer گیر کرد:

```bash
devfix connect snowflake
```

صبر کن تا دقیقاً این پیام را ببینی و Shell Prompt دوباره برگردد:

```text
Connected with built-in Snowflake.
```

بعد دستور موردنظر را از Wrapper مناسب DevFix اجرا کن.

### اتصال، وضعیت و قطع

```bash
devfix connect snowflake
devfix status
devfix disconnect
```

برای restart مسیر:

```bash
devfix restart
```

DevFix را لازم نیست همیشه روشن نگه داری. اگر Direct قابل استفاده است، معمولاً سریع‌تر است.

---

## Homebrew

روی این Mac ترجیحاً از Wrapper خود DevFix استفاده کن:

```bash
devfix brew update
devfix brew outdated
devfix brew install <formula>
devfix brew cleanup
devfix brew doctor
```

### Update با Upgrade فرق دارد

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

اگر `outdated` خالی است، upgrade کلی لازم نیست.

### هشدار Monterey / Tier 3

هشدار macOS 12 / Tier 3 به‌تنهایی به معنی خرابی Homebrew نیست. بعضی Formulaهای جدید روی Intel Monterey Bottle سازگار ندارند و به source build می‌روند؛ بنابراین هر خطای install لزوماً مشکل اینترنت یا DevFix نیست.

---

## GitHub CLI — gh

`gh` در این سیستم مستقیم نصب شده است:

```text
/usr/local/bin/gh
```

بررسی نسخه و Login:

```bash
gh --version
gh auth status
```

خاموش کردن DevFix باعث Logout شدن `gh` نمی‌شود:

```text
gh login = هویت و Credential GitHub
DevFix   = فقط مسیر شبکه
```

اگر `gh` مستقیم کار می‌کند، DevFix لازم نیست. اگر مسیر شبکه مشکل داشت:

```bash
devfix run gh <command>
```

مثال:

```bash
devfix run gh auth status
```

---

## Git

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

## curl و دانلود

اگر URL مستقیم قابل دسترس است:

```bash
curl -fL -O <URL>
```

اگر مسیر مستقیم مشکل دارد:

```bash
devfix curl -fL -O <URL>
```

برای اتصال ناپایدار، Retry محدود و مشخص استفاده کن؛ برای نمونه:

```bash
devfix curl --http1.1 -fL \
  --retry 10 \
  --retry-all-errors \
  --retry-delay 3 \
  -O <URL>
```

اگر یک فایل کوچک با Snowflake ETA چندساعته نشان می‌دهد، کورکورانه منتظر نمان؛ در صورت امکان Direct را مقایسه کن.

---

## اجرای هر CLI از مسیر DevFix

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

---

## آیا DevFix می‌تواند یک سایت یا IP محدودشده را باز کند؟

برای یک درخواست CLI، در صورتی که مقصد از Tor/Snowflake قابل دسترسی باشد:

```bash
devfix curl https://example.com
devfix curl https://1.2.3.4
```

اما نسخه فعلی VPN سراسری یا Browser VPN نیست و Safari/Chrome را خودکار Proxy نمی‌کند.

---

## External Proxy

اگر یک Proxy خارجی معتبر داری، DevFix می‌تواند از آن استفاده کند:

```bash
devfix proxy set socks5h://127.0.0.1:1080
devfix connect external-proxy
```

این بخش برای استفاده از یک Proxy واقعی موجود است؛ DevFix خودش یک IP Proxy دلخواه تولید نمی‌کند.

---

## Transportها

```bash
devfix transport list
devfix transport status
devfix transport test direct
devfix transport test snowflake
devfix transport auto
```

---

## اگر Snowflake گیر کرد

اگر bootstrap زیر 100٪ متوقف شد، آن را transport/bootstrap failure در نظر بگیر. اگر Tor به 100٪ رسید ولی endpoint validation شکست خورد، route-validation failure است. این دو را یکی ندان.

یک Session خراب Snowflake لزوماً به معنی خرابی DevFix نیست. با اینترنت پایدار و retry محدود دوباره امتحان کن؛ Wi-Fi/Hotspot را وسط Bootstrap یا Download عوض نکن.

---

## Log و عیب‌یابی

```bash
devfix logs --tail 200
devfix doctor
devfix doctor --verbose
```

قبل از انتشار Log در فضای عمومی آن را مرور کن.

---

## FFmpeg و FFprobe

این دو مستقیم نصب شده‌اند، نه توسط Homebrew:

```text
/usr/local/bin/ffmpeg
/usr/local/bin/ffprobe
```

بررسی:

```bash
ffmpeg -version
ffprobe -version
```

`brew upgrade` آن‌ها را آپدیت نمی‌کند؛ نسخه Direct باید جداگانه بررسی و به‌روزرسانی شود.

`gh` نیز Direct install است و Homebrew آن را آپدیت نمی‌کند.

قبل از اجرای `brew install gh` یا `brew install ffmpeg` بررسی کن Direct install موجود با Homebrew conflict نکند.

---

## چیزهایی که نباید بی‌دلیل انجام دهی

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

## مدل ذهنی ساده

```text
GitHub Login
  → gh Credential در Keychain
  → ماندگار است و با devfix disconnect از بین نمی‌رود

DevFix
  → فقط مسیر شبکه است
  → فقط وقتی لازم است روشنش کن
```

و:

```text
Direct کار می‌کند؟
  بله → Direct استفاده کن
  نه  → devfix connect snowflake
        سپس devfix brew / git / curl / run
        و بعد از پایان کار devfix disconnect
```

## قانون نهایی

DevFix را «ابزار شبکه برای Developer CLIها» در نظر بگیر، نه VPN دائمی کل مک. اگر مستقیم کار می‌کند، مستقیم برو. اگر Developer endpoint محدود/ناپایدار است Snowflake را روشن کن. اگر Homebrew خطا داد، اول مشخص کن مشکل Network است یا Compatibility/Formula؛ کورکورانه reinstall یا upgrade نکن.
