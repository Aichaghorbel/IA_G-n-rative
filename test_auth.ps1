# SmartCampus AI - verification de l'authentification, des roles et du chat libre
# Usage (PowerShell, depuis le dossier du projet) :
#   powershell -ExecutionPolicy Bypass -File .\test_auth.ps1
# Prerequis : docker compose up -d  (backend sur http://localhost:8000)

$Base      = "http://localhost:8000/api/v1"
$AdminMail = "admin@smartcampus.tn"
$AdminPass = "AdminSmartCampus2026!"
$Strong    = "Str0ngPassw0rd!"
$NewPass   = "N3wStr0ngPass!"
$Run       = Get-Date -Format "HHmmss"

$script:pass = 0
$script:fail = 0

function Call {
    param([string]$Method, [string]$Path, $Body = $null, [hashtable]$Headers = @{})
    $p = @{ Uri = "$Base$Path"; Method = $Method; Headers = $Headers; UseBasicParsing = $true }
    if ($Body -ne $null) { $p.Body = ($Body | ConvertTo-Json -Depth 5); $p.ContentType = "application/json" }
    try {
        $r = Invoke-WebRequest @p
        $json = $null
        if ($r.Content) { try { $json = $r.Content | ConvertFrom-Json } catch {} }
        return @{ Status = [int]$r.StatusCode; Json = $json; Headers = $r.Headers }
    } catch {
        $status = 0; $raw = $null
        if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $raw = $_.ErrorDetails.Message }
        else {
            try {
                $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $raw = $sr.ReadToEnd()
            } catch {}
        }
        $json = $null
        if ($raw) { try { $json = $raw | ConvertFrom-Json } catch {} }
        return @{ Status = $status; Json = $json; Headers = @{} }
    }
}

function Check {
    param([string]$Name, [bool]$Condition, [string]$Detail = "")
    if ($Condition) { $script:pass++; Write-Host ("[PASS] " + $Name) -ForegroundColor Green }
    else { $script:fail++; Write-Host ("[FAIL] " + $Name + "  " + $Detail) -ForegroundColor Red }
}

function Bearer($t) { return @{ Authorization = "Bearer $t" } }
function HeaderValue($h, $name) {
    $v = $h[$name]
    if ($v -is [array]) { $v = $v[0] }
    return $v
}

Write-Host "`n=== 0. Sante de l'API ===" -ForegroundColor Cyan
$r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
Check "GET /health -> 200" ($r -and $r.StatusCode -eq 200)
if (-not $r) { Write-Host "Backend injoignable. Lancez: docker compose up -d" -ForegroundColor Yellow; exit 1 }

# ---------------------------------------------------------------------------
Write-Host "`n=== 1. Chat libre pour les visiteurs SANS compte ===" -ForegroundColor Cyan
$a = Call POST "/conversations"
$tokA = HeaderValue $a.Headers "X-Session-Token"
Check "POST /conversations sans aucun jeton -> 201" ($a.Status -eq 201) "statut=$($a.Status)"
Check "Le jeton visiteur est renvoye (X-Session-Token)" ([bool]$tokA)
$convA = $a.Json.conversation_id

$m = Call POST "/conversations/$convA/messages" @{ message = "Quelles formations propose l'IIT ?" } @{ "X-Session-Token" = $tokA }
Check "Le visiteur envoie un message -> 200 avec reponse" ($m.Status -eq 200 -and $m.Json.response) "statut=$($m.Status)"

$h = Call GET "/conversations/$convA/messages" $null @{ "X-Session-Token" = $tokA }
Check "Historique visible par son proprietaire (2 elements)" ($h.Status -eq 200 -and @($h.Json).Count -eq 2) "statut=$($h.Status)"

$b = Call POST "/conversations"
$tokB = HeaderValue $b.Headers "X-Session-Token"
$x = Call GET "/conversations/$convA" $null @{ "X-Session-Token" = $tokB }
Check "Un autre visiteur ne peut PAS lire cette conversation -> 404" ($x.Status -eq 404) "statut=$($x.Status)"
$x = Call DELETE "/conversations/$convA" $null @{ "X-Session-Token" = $tokB }
Check "Un autre visiteur ne peut PAS la supprimer -> 404" ($x.Status -eq 404) "statut=$($x.Status)"

# ---------------------------------------------------------------------------
Write-Host "`n=== 2. Protection des API : 401 sans jeton, 403 pour le visiteur ===" -ForegroundColor Cyan
$x = Call GET "/candidates"
Check "GET /candidates sans jeton -> 401" ($x.Status -eq 401) "statut=$($x.Status)"
$x = Call GET "/admin/metrics"
Check "GET /admin/metrics sans jeton -> 401" ($x.Status -eq 401) "statut=$($x.Status)"
$x = Call GET "/candidates" $null @{ "X-Session-Token" = $tokA }
Check "GET /candidates avec session visiteur -> 403" ($x.Status -eq 403) "statut=$($x.Status)"

# ---------------------------------------------------------------------------
Write-Host "`n=== 3. Connexion du responsable (Administrateur) ===" -ForegroundColor Cyan
$x = Call POST "/auth/login" @{ email = $AdminMail; password = "MauvaisMotDePasse1" }
Check "Mauvais mot de passe -> 401 AUTH_INVALID_CREDENTIALS" ($x.Status -eq 401 -and $x.Json.error.code -eq "AUTH_INVALID_CREDENTIALS") "statut=$($x.Status)"

$login = Call POST "/auth/login" @{ email = $AdminMail; password = $AdminPass }
Check "Connexion admin -> 200, role Administrateur" ($login.Status -eq 200 -and $login.Json.role -eq "Administrateur") "statut=$($login.Status)"
if ($login.Status -ne 200) { Write-Host "Impossible de continuer sans admin (compte absent ? migration 04 appliquee ?)." -ForegroundColor Yellow; exit 1 }
$adm = $login.Json.access_token

$me = Call GET "/auth/me" $null (Bearer $adm)
Check "GET /auth/me -> 200 avec permissions" ($me.Status -eq 200 -and $me.Json.permissions) "statut=$($me.Status)"

$x = Call GET "/auth/me" $null (Bearer $login.Json.refresh_token)
Check "Un refresh token ne peut PAS servir de jeton d'acces -> 401" ($x.Status -eq 401) "statut=$($x.Status)"

$x = Call GET "/auth/me" $null @{ Authorization = "Bearer abc.def.ghi" }
Check "Jeton falsifie -> 401" ($x.Status -eq 401) "statut=$($x.Status)"

$x = Call GET "/admin/metrics" $null (Bearer $adm)
Check "Admin sur /admin/metrics -> accepte (ni 401 ni 403)" ($x.Status -ne 401 -and $x.Status -ne 403) "statut=$($x.Status)"

# ---------------------------------------------------------------------------
Write-Host "`n=== 4. Comptes du personnel (cree par l'admin) ===" -ForegroundColor Cyan
$tMail = "enseignant.test$Run@smartcampus.tn"
$x = Call POST "/auth/users" @{ email = $tMail; password = "faible"; nom = "Test"; prenom = "Ens"; role = "Enseignant" } (Bearer $adm)
Check "Mot de passe faible refuse -> 422" ($x.Status -eq 422) "statut=$($x.Status)"
$x = Call POST "/auth/users" @{ email = $tMail; password = $Strong; nom = "Test"; prenom = "Ens"; role = "Candidat" } (Bearer $adm)
Check "Creer un role Candidat via cette route refuse -> 422" ($x.Status -eq 422) "statut=$($x.Status)"
$x = Call POST "/auth/users" @{ email = "autre.admin$Run@smartcampus.tn"; password = $Strong; nom = "Test"; prenom = "Adm"; role = "Administrateur" } (Bearer $adm)
Check "Administrateur unique : creer un 2e admin refuse -> 422" ($x.Status -eq 422) "statut=$($x.Status)"
$x = Call POST "/auth/users" @{ email = $tMail; password = $Strong; nom = "Test"; prenom = "Ens"; role = "Enseignant" } (Bearer $adm)
Check "Creation d'un enseignant -> 201" ($x.Status -eq 201) "statut=$($x.Status)"
$x = Call POST "/auth/users" @{ email = $tMail; password = $Strong; nom = "Test"; prenom = "Ens"; role = "Enseignant" } (Bearer $adm)
Check "E-mail en double -> 409" ($x.Status -eq 409) "statut=$($x.Status)"

$tl = Call POST "/auth/login" @{ email = $tMail; password = $Strong }
Check "Connexion enseignant -> 200, changement de mot de passe exige" ($tl.Status -eq 200 -and $tl.Json.must_change_password -eq $true) "statut=$($tl.Status)"
$x = Call GET "/candidates" $null (Bearer $tl.Json.access_token)
Check "Mot de passe temporaire : routes bloquees -> 403 AUTH_010" ($x.Status -eq 403 -and $x.Json.error.code -eq "AUTH_010") "statut=$($x.Status)"

$x = Call POST "/auth/change-password" @{ current_password = $Strong; new_password = $NewPass } (Bearer $tl.Json.access_token)
Check "Changement de mot de passe -> 204" ($x.Status -eq 204) "statut=$($x.Status)"
$x = Call GET "/auth/me" $null (Bearer $tl.Json.access_token)
Check "Ancien jeton invalide apres changement de mot de passe -> 401" ($x.Status -eq 401) "statut=$($x.Status)"

$tl = Call POST "/auth/login" @{ email = $tMail; password = $NewPass }
$teach = $tl.Json.access_token
Check "Reconnexion enseignant avec le nouveau mot de passe -> 200" ($tl.Status -eq 200 -and $tl.Json.must_change_password -eq $false) "statut=$($tl.Status)"

# ---------------------------------------------------------------------------
Write-Host "`n=== 5. Matrice des roles ===" -ForegroundColor Cyan
$x = Call GET "/admin/metrics" $null (Bearer $teach)
Check "Enseignant sur /admin/metrics -> 403" ($x.Status -eq 403) "statut=$($x.Status)"
$x = Call POST "/auth/users" @{ email = "x$Run@smartcampus.tn"; password = $Strong; nom = "A"; prenom = "B"; role = "Enseignant" } (Bearer $teach)
Check "Enseignant ne peut pas creer de comptes -> 403" ($x.Status -eq 403) "statut=$($x.Status)"
$x = Call GET "/candidates/me" $null (Bearer $teach)
Check "Enseignant sur /candidates/me (route candidat) -> 403" ($x.Status -eq 403) "statut=$($x.Status)"
$x = Call POST "/conversations" $null (Bearer $teach)
Check "Enseignant ne peut pas ouvrir de chat -> 403" ($x.Status -eq 403) "statut=$($x.Status)"
$x = Call GET "/conversations/$convA/messages" $null (Bearer $teach)
Check "Enseignant ne lit pas une conversation sans lien avec lui -> 404" ($x.Status -eq 404) "statut=$($x.Status)"

# ---------------------------------------------------------------------------
Write-Host "`n=== 6. Conversion visiteur -> candidat ===" -ForegroundColor Cyan
$cMail = "candidat.test$Run@gmail.com"
$body = @{ session_id = "sess_demo_$Run"; email = $cMail; nom = "Candidat"; prenom = "Test" }
$x = Call POST "/auth/convert" $body
Check "Convert sans jeton -> 401" ($x.Status -eq 401) "statut=$($x.Status)"
$x = Call POST "/auth/convert" $body @{ "X-Session-Token" = $tokA }
Check "Convert par un visiteur -> 403" ($x.Status -eq 403) "statut=$($x.Status)"
$conv = Call POST "/auth/convert" $body (Bearer $teach)
Check "Convert par un enseignant -> 201 + mot de passe temporaire" ($conv.Status -eq 201 -and $conv.Json.temporary_password) "statut=$($conv.Status)"

$cl = Call POST "/auth/login" @{ email = $cMail; password = $conv.Json.temporary_password }
Check "Connexion du candidat -> 200, role Candidat" ($cl.Status -eq 200 -and $cl.Json.role -eq "Candidat") "statut=$($cl.Status)"
Check "Candidat : changement de mot de passe obligatoire" ($cl.Json.must_change_password -eq $true)
$x = Call POST "/auth/change-password" @{ current_password = $conv.Json.temporary_password; new_password = $NewPass } (Bearer $cl.Json.access_token)
$cl = Call POST "/auth/login" @{ email = $cMail; password = $NewPass }
$cand = $cl.Json.access_token
Check "Candidat reconnecte avec son nouveau mot de passe" ($cl.Status -eq 200 -and $cl.Json.must_change_password -eq $false)

$x = Call GET "/admin/metrics" $null (Bearer $cand)
Check "Candidat sur /admin/metrics -> 403" ($x.Status -eq 403) "statut=$($x.Status)"
$x = Call GET "/candidates" $null (Bearer $cand)
Check "Candidat sur la liste des candidats -> 403" ($x.Status -eq 403) "statut=$($x.Status)"
$x = Call POST "/auth/users" @{ email = "y$Run@smartcampus.tn"; password = $Strong; nom = "A"; prenom = "B"; role = "Enseignant" } (Bearer $cand)
Check "Candidat ne peut pas creer de comptes -> 403" ($x.Status -eq 403) "statut=$($x.Status)"

$cc = Call POST "/conversations" $null (Bearer $cand)
Check "Candidat connecte peut utiliser le chat -> 201" ($cc.Status -eq 201) "statut=$($cc.Status)"
if ($cc.Status -eq 201) {
    $x = Call GET "/conversations/$($cc.Json.conversation_id)" $null @{ "X-Session-Token" = $tokA }
    Check "Un visiteur ne lit pas la conversation d'un candidat -> 404" ($x.Status -eq 404) "statut=$($x.Status)"
}

# ---------------------------------------------------------------------------
Write-Host "`n=== 7. Refresh avec rotation et deconnexion ===" -ForegroundColor Cyan
$cl2 = Call POST "/auth/login" @{ email = $cMail; password = $NewPass }
$old = $cl2.Json.refresh_token
$ref = Call POST "/auth/refresh" @{ refresh_token = $old }
Check "Refresh -> 200, role Candidat conserve" ($ref.Status -eq 200 -and $ref.Json.role -eq "Candidat" -and $ref.Json.user_id -gt 0) "statut=$($ref.Status)"
$x = Call POST "/auth/refresh" @{ refresh_token = $old }
Check "Rejouer l'ancien refresh token -> 401" ($x.Status -eq 401) "statut=$($x.Status)"

$lg = Call POST "/auth/login" @{ email = $cMail; password = $NewPass }
$tokOut = $lg.Json.access_token
$x = Call POST "/auth/logout" $null (Bearer $tokOut)
Check "Deconnexion -> 204" ($x.Status -eq 204) "statut=$($x.Status)"
$x = Call GET "/auth/me" $null (Bearer $tokOut)
Check "Jeton revoque apres deconnexion -> 401" ($x.Status -eq 401) "statut=$($x.Status)"

# ---------------------------------------------------------------------------
Write-Host "`n=== 8. Verrouillage apres echecs repetes ===" -ForegroundColor Cyan
$lMail = "verrou.test$Run@smartcampus.tn"
$x = Call POST "/auth/users" @{ email = $lMail; password = $Strong; nom = "Verrou"; prenom = "Test"; role = "Enseignant" } (Bearer $adm)
1..5 | ForEach-Object { $null = Call POST "/auth/login" @{ email = $lMail; password = "Mauvais$_" } }
$x = Call POST "/auth/login" @{ email = $lMail; password = $Strong }
Check "6e tentative (meme avec le bon mot de passe) -> 423 verrouille" ($x.Status -eq 423) "statut=$($x.Status)"

# ---------------------------------------------------------------------------
Write-Host "`n=== 9. Verification OTP par e-mail ===" -ForegroundColor Cyan
$oMail = "otp.test$Run@gmail.com"
$o = Call POST "/auth/otp/request" @{ email = $oMail }
Check "Demande OTP -> 200" ($o.Status -eq 200) "statut=$($o.Status)"
$x = Call POST "/auth/otp/request" @{ email = $oMail }
Check "Redemande immediate -> 429 (delai entre envois)" ($x.Status -eq 429) "statut=$($x.Status)"
$code = $o.Json.dev_code
if ($code) {
    $x = Call POST "/auth/otp/verify" @{ email = $oMail; otp_code = $code }
    Check "Bon code -> 200 + verification_token" ($x.Status -eq 200 -and $x.Json.verification_token) "statut=$($x.Status)"
    $x = Call POST "/auth/otp/verify" @{ email = $oMail; otp_code = $code }
    Check "Meme code reutilise -> 400 (usage unique)" ($x.Status -eq 400) "statut=$($x.Status)"
} else {
    Write-Host "[SKIP] dev_code absent (DEBUG desactive) : lisez le code dans Mailpit http://localhost:8025" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
Write-Host "`n=== 10. Desactivation d'un compte ===" -ForegroundColor Cyan
$list = Call GET "/auth/users?limit=100" $null (Bearer $adm)
$target = @($list.Json) | Where-Object { $_.email -eq $tMail } | Select-Object -First 1
if ($target) {
    $x = Call PATCH "/auth/users/$($target.id)" @{ is_active = $false } (Bearer $adm)
    Check "Admin desactive l'enseignant -> 200" ($x.Status -eq 200 -and $x.Json.is_active -eq $false) "statut=$($x.Status)"
    $x = Call GET "/auth/me" $null (Bearer $teach)
    Check "Son jeton en cours est coupe immediatement -> 401" ($x.Status -eq 401) "statut=$($x.Status)"
    $x = Call POST "/auth/login" @{ email = $tMail; password = $NewPass }
    Check "Il ne peut plus se connecter -> 401" ($x.Status -eq 401) "statut=$($x.Status)"
} else {
    Check "Compte enseignant retrouve dans la liste" $false "introuvable"
}
$meId = $me.Json.id
$x = Call PATCH "/auth/users/$meId" @{ is_active = $false } (Bearer $adm)
Check "Un admin ne peut pas se desactiver lui-meme -> 409" ($x.Status -eq 409) "statut=$($x.Status)"

# ---------------------------------------------------------------------------
Write-Host "`n==================== RESULTAT ====================" -ForegroundColor Cyan
Write-Host ("PASS : " + $script:pass) -ForegroundColor Green
if ($script:fail -gt 0) { Write-Host ("FAIL : " + $script:fail) -ForegroundColor Red } else { Write-Host "FAIL : 0" -ForegroundColor Green }
if ($script:fail -gt 0) { exit 1 }
