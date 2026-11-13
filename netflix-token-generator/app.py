import re
import urllib.parse
import requests
from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

# إعدادات Netflix API
NFTOKEN_API_URL = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"

NFTOKEN_QUERY_PARAMS = {
    "appVersion": "15.48.1",
    "config": '{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false","cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true","addHorizontalBoxArtToVideoSummariesEnabled":"false","skOverlayTestEnabled":"false","homeFeedTestTVMovieListsEnabled":"false","baselineOnIpadEnabled":"true","trailersVideoIdLoggingFixEnabled":"true","postPlayPreviewsEnabled":"false","bypassContextualAssetsEnabled":"false","roarEnabled":"false","useSeason1AltLabelEnabled":"false","disableCDSSearchPaginationSectionKinds":["searchVideoCarousel"],"cdsSearchHorizontalPaginationEnabled":"true","searchPreQueryGamesEnabled":"true","kidsMyListEnabled":"true","billboardEnabled":"true","useCDSGalleryEnabled":"true","contentWarningEnabled":"true","videosInPopularGamesEnabled":"true","avifFormatEnabled":"false","sharksEnabled":"true"}',
    "device_type": "NFAPPL-02-",
    "esn": "NFAPPL-02-IPHONE8%3D1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "idiom": "phone",
    "iosVersion": "15.8.5",
    "isTablet": "false",
    "languages": "en-US",
    "locale": "en-US",
    "maxDeviceWidth": "375",
    "model": "saget",
    "modelType": "IPHONE8-1",
    "odpAware": "true",
    "path": '["account","token","default"]',
    "pathFormat": "graph",
    "pixelDensity": "2.0",
    "progressive": "false",
    "responseFormat": "json",
}

NFTOKEN_HEADERS = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "x-netflix.request.attempt": "1",
    "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.argo.translated": "true",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.context.max-device-width": "375",
    "x-netflix.context.ab-tests": "",
    "x-netflix.tracing.cl.useractionid": "4DC655F2-9C3C-4343-8229-CA1B003C3053",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "x-netflix.context.locales": "en-US",
    "x-netflix.context.top-level-uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.client.iosversion": "15.8.5",
    "accept-language": "en-US;q=1",
    "x-netflix.argo.abtests": "",
    "x-netflix.context.os-version": "15.8.5",
    "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo",
    "x-netflix.argo.nfnsm": "9",
    "x-netflix.context.pixel-density": "2.0",
    "x-netflix.request.toplevel.uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.request.client.timezoneid": "Asia/Dhaka",
}

def parse_netscape_cookies(cookie_text: str) -> dict:
    """استخراج الكوكيز بذكاء يدعم المسافات والتاب وأي تنسيق."""
    cookies = {}
    
    # البحث المباشر بالـ Regex
    netflix_id_match = re.search(r'\bNetflixId[=\s]+([^\s]+)', cookie_text)
    if netflix_id_match:
        cookies['NetflixId'] = netflix_id_match.group(1).strip('"\'')
        
    secure_netflix_id_match = re.search(r'\bSecureNetflixId[=\s]+([^\s]+)', cookie_text)
    if secure_netflix_id_match:
        cookies['SecureNetflixId'] = secure_netflix_id_match.group(1).strip('"\'')
        
    # كود احتياطي لتحليل السطور
    for line in cookie_text.strip().splitlines():
        line = line.strip()
        if not line or (line.startswith('#') and not line.startswith('#HttpOnly_')):
            continue
        if line.startswith('#HttpOnly_'):
            line = line[len('#HttpOnly_'):]
        
        fields = line.split() 
        if len(fields) >= 7:
            name = fields[5].strip()
            value = fields[6].strip()
            if name and value:
                cookies[name] = value
        elif '=' in line:
            name, value = line.split('=', 1)
            cookies[name.strip()] = value.strip()

    return cookies

def generate_nftoken(session: requests.Session):
    """استخراج التوكن من الهيكل المتداخل الجديد لـ Netflix."""
    try:
        resp = session.get(
            NFTOKEN_API_URL,
            params=NFTOKEN_QUERY_PARAMS,
            headers=NFTOKEN_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        
        # الهيكل الجديد: value -> account -> token -> default -> token
        token_data = (((data.get("value") or {}).get("account") or {})
                      .get("token") or {}).get("default") or {}
        
        nftoken = token_data.get("token")
        
        # حلول احتياطية في حال تغير الهيكل مستقبلاً
        if not nftoken:
            nftoken = data.get('token') or data.get('nftoken')
            if not nftoken:
                nftoken = (data.get('value') or {}).get('token')
                
        return nftoken
    except Exception:
        return None

def validate_and_generate(cookie_text: str):
    cookies = parse_netscape_cookies(cookie_text)
    
    netflix_id = cookies.get('NetflixId')
    secure_netflix_id = cookies.get('SecureNetflixId')

    if not netflix_id or not secure_netflix_id:
        return False, "Missing required cookies: NetflixId and/or SecureNetflixId. Please check your input."

    # فك تشفير URL إن وجد
    netflix_id = urllib.parse.unquote(netflix_id)
    secure_netflix_id = urllib.parse.unquote(secure_netflix_id)

    session = requests.Session()
    session.cookies.set('NetflixId', netflix_id, domain='.netflix.com')
    session.cookies.set('SecureNetflixId', secure_netflix_id, domain='.netflix.com')
    
    if cookies.get('gsid'):
        session.cookies.set('gsid', cookies['gsid'], domain='.netflix.com')
    if cookies.get('nfvdid'):
        session.cookies.set('nfvdid', cookies['nfvdid'], domain='.netflix.com')

    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    # التحقق من الكوكيز
    try:
        resp = session.get('https://www.netflix.com/YourAccount', timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')
        if soup.find(string=re.compile('Sign In', re.I)):
            return False, "Invalid or expired cookies (redirected to Sign In)."
    except Exception as e:
        return False, f"Error validating cookies: {str(e)}"

    # توليد التوكن
    nftoken = generate_nftoken(session)
    if not nftoken:
        return False, "Failed to generate NFToken. Cookies may be valid but the token endpoint failed."

    # إنشاء الروابط
    encoded_token = urllib.parse.quote(nftoken, safe='')
    links = {
        'pc': f'https://www.netflix.com/browse?nftoken={encoded_token}',
        'mobile': f'https://www.netflix.com/unsupported?nftoken={encoded_token}',
        'tv': f'https://www.netflix.com/tv8?nftoken={encoded_token}',
    }
    return True, {'nftoken': nftoken, 'links': links}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    cookie_text = request.form.get('cookie_text', '').strip()
    if not cookie_text:
        return jsonify({'error': 'Cookie text is required.'}), 400

    success, result = validate_and_generate(cookie_text)
    if success:
        return jsonify(result)
    else:
        return jsonify({'error': result}), 401

if __name__ == '__main__':
    app.run(debug=True)