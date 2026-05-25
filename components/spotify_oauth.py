import os
import webbrowser
import urllib.parse
import base64
import hashlib
import secrets
import requests
import ssl
import tempfile
import ipaddress
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_API_KEY")
REDIRECT_URI = "https://127.0.0.1:8443/callback"
SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/callback'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'code' in params:
                self.server.auth_code = params['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write('<html><body><h1>Authorization successful!</h1><p>You can close this window.</p></body></html>'.encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write('<html><body><h1>Authorization failed!</h1></body></html>'.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def generate_code_verifier():
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

def generate_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

def create_self_signed_cert(): # FULLY VIBE-CODED CERT
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"127.0.0.1"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(u"localhost"),
                x509.IPAddress(ipaddress.IPv4Address(u"127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        cert_file = tempfile.NamedTemporaryFile(mode='w+b', suffix='.pem', delete=False)
        key_file = tempfile.NamedTemporaryFile(mode='w+b', suffix='.key', delete=False)
        
        cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
        key_file.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
        
        cert_file.close()
        key_file.close()
        
        return cert_file.name, key_file.name
        
    except ImportError:
        print("cryptography library not found. Install with: pip install cryptography")
        print("Falling back to HTTP (less secure)")
        return None, None

def start_auth_server(): # STARTS A LOCAL HTTPS SERVER FOR AUTH
    global REDIRECT_URI
    
    cert_file, key_file = create_self_signed_cert()
    
    if cert_file and key_file:
        server = HTTPServer(('127.0.0.1', 8443), AuthHandler)
        server.auth_code = None
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        
        print("HTTPS server started with self-signed certificate on 127.0.0.1:8443")
        print("You may see a browser security warning - this is normal for self-signed certificates")
        print("Server will accept connections at https://127.0.0.1:8443/callback")
        
    original_shutdown = server.shutdown
    def shutdown_with_cleanup():
            try:
                os.unlink(cert_file)
                os.unlink(key_file)
            except:
                pass
            original_shutdown()
    server.shutdown = shutdown_with_cleanup
        
      
    # Start server in a separate thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    return server

def get_user_authorization():
    if not CLIENT_ID:
        raise ValueError("SPOTIFY_API_KEY not found in environment variables")
    
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    
    print("Starting local server for OAuth callback...")
    server = start_auth_server()
    
    # Create auth URL with proper encoding
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'code_challenge_method': 'S256',
        'code_challenge': code_challenge
    }
    
    auth_url = f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
    
    print(f"Authorization URL: {auth_url}")
    print(f" Redirect URI being used: {REDIRECT_URI}")

    
    webbrowser.open(auth_url)
    
    print("Waiting for authorization...")
    timeout = 120
    start_time = time.time()
    
    while server.auth_code is None and (time.time() - start_time) < timeout:
        time.sleep(1)
    
    if server.auth_code is None:
        server.shutdown()
        raise TimeoutError("Authorization timed out")
    
    auth_code = server.auth_code
    server.shutdown()
    
    token_data = exchange_code_for_tokens(auth_code, code_verifier)
    
    if token_data:
        save_tokens(token_data)
        print("Authorization successful! Tokens saved.")
        return token_data
    else:
        raise Exception("Failed to exchange authorization code for tokens")

def exchange_code_for_tokens(auth_code, code_verifier):
    token_url = "https://accounts.spotify.com/api/token"
    
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'code_verifier': code_verifier
    }
    
    try:
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"Token exchange successful")
            return token_data
        else:
            return None
    except Exception as e:
        print(f"Error during token exchange: {e}")
        return None

def save_tokens(token_data):
    token_file = os.path.join(os.path.dirname(__file__), '..', 'spotify_tokens.txt')
    try:
        with open(token_file, 'w', encoding='utf-8') as f:
            f.write(f"access_token={token_data.get('access_token', '')}\n")
            f.write(f"refresh_token={token_data.get('refresh_token', '')}\n")
            f.write(f"expires_in={token_data.get('expires_in', '')}\n")
            f.write(f"token_type={token_data.get('token_type', '')}\n")
    except Exception as e:
        raise

def load_tokens():
    token_file = os.path.join(os.path.dirname(__file__), '..', 'spotify_tokens.txt')
    if not os.path.exists(token_file):
        return None
    
    tokens = {}
    try:
        with open(token_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    tokens[key] = value
        return tokens
    except Exception as e:
        return None

def refresh_access_token(refresh_token):
    token_url = "https://accounts.spotify.com/api/token"
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID
    }
    
    try:
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
          
            existing_tokens = load_tokens()
            if existing_tokens:
                existing_tokens['access_token'] = token_data.get('access_token', existing_tokens.get('access_token', ''))
                if 'refresh_token' in token_data:
                    existing_tokens['refresh_token'] = token_data['refresh_token']
                if 'expires_in' in token_data:
                    existing_tokens['expires_in'] = token_data['expires_in']
                if 'token_type' in token_data:
                    existing_tokens['token_type'] = token_data['token_type']
                save_tokens(existing_tokens)
            else:
                save_tokens(token_data)
            return token_data.get('access_token')
        else:
            print(f"Token refresh failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error during token refresh: {e}")
        return None

def get_valid_access_token():
    tokens = load_tokens()
    
    if not tokens:
        token_data = get_user_authorization()
        return token_data['access_token']
    
    access_token = refresh_access_token(tokens['refresh_token'])
    
    if not access_token:
        token_data = get_user_authorization()
        return token_data['access_token']
    
    return access_token

if __name__ == "__main__":
    try:
        token = get_valid_access_token()
        print(f"Successfully obtained access token: {token[:20]}...")
    except Exception as e:
        print(f"Authorization failed: {e}")
