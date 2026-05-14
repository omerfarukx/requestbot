# RequestBot E2E API Test
# Kullanim: .\test-e2e.ps1
# Farkli admin: .\test-e2e.ps1 -AdminUser admin -AdminPass sifre
param(
  [string]$AdminUser = "omerfaruk",
  [string]$AdminPass = "0120dunya"
)

$ErrorActionPreference = "Stop"
$BASE = "http://localhost:8001"
$ts = [int]([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
$EMAIL = "test$ts@bot.com"
$BOT_USER = "testuser$ts"
$PASS = "test1234"

function Step($n, $msg) { Write-Host "`n[$n] $msg" -ForegroundColor Cyan }
function OK($msg)      { Write-Host "  OK   $msg" -ForegroundColor Green }
function Fail($msg)    { Write-Host "  FAIL $msg" -ForegroundColor Red; exit 1 }

Write-Host "=== RequestBot E2E Test ===" -ForegroundColor Yellow
Write-Host "Server: $BASE"
Write-Host "User  : $BOT_USER / $PASS`n"

# ----- 1. Server up? -----
Step 1 "Server saglik kontrolu"
try {
  $null = Invoke-RestMethod "$BASE/docs" -Method GET -TimeoutSec 3
  OK "Server ayakta"
} catch { Fail "Server erisilemez: $_" }

# ----- 2. Register -----
Step 2 "Yeni kullanici kaydi"
$body = @{ email = $EMAIL; username = $BOT_USER; password = $PASS } | ConvertTo-Json
try {
  $reg = Invoke-RestMethod "$BASE/api/auth/register" -Method POST -Body $body -ContentType "application/json"
  $token = $reg.access_token
  $user  = $reg.user
  OK "Kayit: $($reg.user.username) | role=$($user.role) | plan=$($user.plan)"
  if (-not $token) { Fail "Token donmedi" }
} catch { Fail "Register basarisiz: $_" }

# ----- 3. Login -----
Step 3 "Login dogrulama"
$body = @{ username = $BOT_USER; password = $PASS } | ConvertTo-Json
try {
  $login = Invoke-RestMethod "$BASE/api/auth/login" -Method POST -Body $body -ContentType "application/json"
  OK "Login OK"
} catch { Fail "Login basarisiz: $_" }

# ----- 4. /me -----
Step 4 "Token ile /api/auth/me"
$hdr = @{ Authorization = "Bearer $token" }
try {
  $me = Invoke-RestMethod "$BASE/api/auth/me" -Method GET -Headers $hdr
  OK "Me: $($me.username) | email=$($me.email)"
} catch { Fail "Me basarisiz: $_" }

# ----- 4b. Lisans kontrolu (admin ise zaten hazir, degilse extend yap) -----
Step "4b" "Lisans hazirlik"
if ($user.role -eq "admin") {
  OK "Register admin olarak dondu - agency lisans hazir, extend gerek yok"
  $ahdr = $hdr  # test user kendisi admin
} else {
  Write-Host "  INFO Test user=user role, admin ile extend yapiliyor..." -ForegroundColor Yellow
  $abody = @{ username = $AdminUser; password = $AdminPass } | ConvertTo-Json
  try {
    $al = Invoke-RestMethod "$BASE/api/auth/login" -Method POST -Body $abody -ContentType "application/json"
    $ahdr = @{ Authorization = "Bearer $($al.access_token)" }
    $uid = [int]$reg.user.id
    if (-not $uid) { Fail "Test user ID alinamadi" }
    $upbody = @{ plan = "pro" } | ConvertTo-Json
    $null = Invoke-RestMethod "$BASE/api/admin/users/$uid" -Method PATCH -Body $upbody -ContentType "application/json" -Headers $ahdr
    $null = Invoke-RestMethod "$BASE/api/admin/users/$uid/extend?days=30" -Method POST -Headers $ahdr
    OK "Test user pro plan + 30 gun lisans verildi"
  } catch { Fail "Admin lisans verme basarisiz: $_" }
}

# ----- 5. License validate (ilk cihaz kilidi) -----
Step 5 "Lisans validate + cihaz kilidi"
$machine1 = "TEST-MACHINE-" + [Guid]::NewGuid().ToString("N").Substring(0, 16)
$body = @{ machine_id = $machine1; hostname = "TEST-PC"; os_info = "Windows 11" } | ConvertTo-Json
try {
  $v = Invoke-RestMethod "$BASE/api/license/validate" -Method POST -Body $body -ContentType "application/json" -Headers $hdr
  if ($v.valid) { OK "Lisans gecerli | plan=$($v.plan) | expires=$($v.expires_at)" }
  else          { Fail "Lisans gecersiz: $($v.reason)" }
} catch { Fail "Validate basarisiz: $_" }

# ----- 6. Heartbeat (ayni cihaz) -----
Step 6 "Heartbeat (ayni cihaz) - OK olmali"
try {
  $v = Invoke-RestMethod "$BASE/api/license/validate" -Method POST -Body $body -ContentType "application/json" -Headers $hdr
  if ($v.valid) { OK "Heartbeat gecti" } else { Fail "Heartbeat reddedildi: $($v.reason)" }
} catch { Fail "Heartbeat basarisiz: $_" }

# ----- 7. Farkli cihaz - reddedilmeli -----
Step 7 "Farkli cihaz ile validate - REDDEDILMELI"
$machine2 = "OTHER-MACHINE-" + [Guid]::NewGuid().ToString("N").Substring(0, 16)
$body2 = @{ machine_id = $machine2; hostname = "OTHER-PC"; os_info = "Windows 11" } | ConvertTo-Json
try {
  $v = Invoke-RestMethod "$BASE/api/license/validate" -Method POST -Body $body2 -ContentType "application/json" -Headers $hdr
  if (-not $v.valid) { OK "Dogru sekilde reddedildi: $($v.reason)" }
  else               { Fail "Farkli cihaz kabul edildi (HATA!)" }
} catch { Fail "Validate hatasi: $_" }

# ----- 8. Device bilgisi -----
Step 8 "Cihaz bilgisi /api/license/device"
try {
  $d = Invoke-RestMethod "$BASE/api/license/device" -Method GET -Headers $hdr
  OK "Cihaz: $($d.hostname) | $($d.os_info) | machine_id=$($d.machine_id.Substring(0,20))..."
} catch { Fail "Device info basarisiz: $_" }

# ----- 8b. Admin reset credit ver -----
Step "8b" "Admin - test user'a 1 reset credit"
try {
  $null = Invoke-RestMethod "$BASE/api/admin/users/$([int]$reg.user.id)/grant-reset" -Method POST -Headers $ahdr
  OK "Reset credit verildi"
} catch { Fail "Grant reset basarisiz: $_" }

# ----- 9. Reset device -----
Step 9 "Cihaz reset + yeni cihaz ile login"
try {
  $r = Invoke-RestMethod "$BASE/api/license/reset-device" -Method POST -Headers $hdr
  OK "Reset OK | kalan hak: $($r.remaining_credits)"
} catch { Fail "Reset basarisiz: $_" }

Step 10 "Reset sonrasi farkli cihaz artik kabul olmali"
try {
  $v = Invoke-RestMethod "$BASE/api/license/validate" -Method POST -Body $body2 -ContentType "application/json" -Headers $hdr
  if ($v.valid) { OK "Yeni cihaz kabul edildi" } else { Fail "Reset sonra da reddedildi: $($v.reason)" }
} catch { Fail "Validate basarisiz: $_" }

# ----- 11. Admin: kullanici listesi -----
Step 11 "Admin - kullanici listesi"
try {
  $users = Invoke-RestMethod "$BASE/api/admin/users" -Method GET -Headers $ahdr
  OK "Toplam $($users.Count) kullanici"
} catch { Fail "Admin erisim hatasi: $_" }

# ----- 12. Download info -----
Step 12 "Download bilgisi"
try {
  $dl = Invoke-RestMethod "$BASE/api/download/info" -Method GET -Headers $hdr
  if ($dl.available) { OK "Dosya hazir: $($dl.filename) ($($dl.size_mb) MB)" }
  else               { OK "Dosya henuz yuklenmedi (beklenen)" }
} catch { Fail "Download info hatasi: $_" }

Write-Host "`n=============================" -ForegroundColor Green
Write-Host " TUM TESTLER BASARILI" -ForegroundColor Green
Write-Host "=============================`n" -ForegroundColor Green
