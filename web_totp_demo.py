import pyotp
import qrcode
import io
import base64
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Template HTML sederhana
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>TOTP Setup</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .qr-code { text-align: center; margin: 20px 0; }
        .secret-info { background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .token-input { padding: 10px; font-size: 16px; margin: 10px; }
        .btn { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .success { color: green; font-weight: bold; }
        .error { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🔐 TOTP (2FA) Setup</h1>
    
    <div class="container">
        <h2>Step 1: Setup 2FA</h2>
        <button class="btn" onclick="generateSetup()">Generate New TOTP Setup</button>
        
        <div id="setup-result" style="display: none;">
            <div class="secret-info">
                <strong>Secret Key:</strong> <span id="secret-key"></span><br>
                <small>Simpan secret key ini dengan aman di database Anda</small>
            </div>
            
            <div class="qr-code">
                <h3>Scan QR Code dengan aplikasi MFA:</h3>
                <img id="qr-image" src="" alt="QR Code" style="border: 1px solid #ddd;">
                <p><small>Google Authenticator, Microsoft Authenticator, Authy, dll.</small></p>
            </div>
        </div>
    </div>
    
    <div class="container">
        <h2>Step 2: Verify Token</h2>
        <input type="text" id="token-input" class="token-input" placeholder="Masukkan 6-digit token" maxlength="6">
        <button class="btn" onclick="verifyToken()">Verify Token</button>
        <div id="verify-result"></div>
    </div>
    
    <div class="container">
        <h2>Step 3: Current Token</h2>
        <button class="btn" onclick="getCurrentToken()">Get Current Token</button>
        <div id="current-token-result"></div>
    </div>

    <script>
        let currentSecret = '';
        
        async function generateSetup() {
            try {
                const response = await fetch('/generate-setup', { method: 'POST' });
                const data = await response.json();
                
                currentSecret = data.secret;
                document.getElementById('secret-key').textContent = data.secret;
                document.getElementById('qr-image').src = 'data:image/png;base64,' + data.qr_code;
                document.getElementById('setup-result').style.display = 'block';
                
            } catch (error) {
                alert('Error generating setup: ' + error.message);
            }
        }
        
        async function verifyToken() {
            const token = document.getElementById('token-input').value;
            if (!currentSecret) {
                alert('Please generate setup first!');
                return;
            }
            
            if (token.length !== 6) {
                alert('Token harus 6 digit!');
                return;
            }
            
            try {
                const response = await fetch('/verify-token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ secret: currentSecret, token: token })
                });
                
                const data = await response.json();
                const resultDiv = document.getElementById('verify-result');
                
                if (data.valid) {
                    resultDiv.innerHTML = '<p class="success">✅ Token VALID!</p>';
                } else {
                    resultDiv.innerHTML = '<p class="error">❌ Token INVALID!</p>';
                }
                
            } catch (error) {
                alert('Error verifying token: ' + error.message);
            }
        }
        
        async function getCurrentToken() {
            if (!currentSecret) {
                alert('Please generate setup first!');
                return;
            }
            
            try {
                const response = await fetch('/current-token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ secret: currentSecret })
                });
                
                const data = await response.json();
                document.getElementById('current-token-result').innerHTML = 
                    '<p><strong>Current Token:</strong> <code>' + data.token + '</code></p>' +
                    '<p><small>Token ini akan berubah setiap 30 detik</small></p>';
                
            } catch (error) {
                alert('Error getting current token: ' + error.message);
            }
        }
    </script>
</body>
</html>
"""

class WebTOTPManager:
    def __init__(self, service_name="MyWebApp"):
        self.service_name = service_name
    
    def generate_setup(self, account_name):
        """Generate TOTP setup dengan QR code untuk web"""
        # Generate secret
        secret = pyotp.random_base32()
        
        # Create TOTP instance
        totp = pyotp.TOTP(secret)
        
        # Generate provisioning URI
        provisioning_uri = totp.provisioning_uri(
            name=account_name,
            issuer_name=self.service_name
        )
        
        # Generate QR code sebagai base64 image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Convert ke image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert ke base64 untuk display di web
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'secret': secret,
            'qr_code': img_base64,
            'provisioning_uri': provisioning_uri
        }
    
    def verify_token(self, secret, token):
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token)
    
    def get_current_token(self, secret):
        """Get current token"""
        totp = pyotp.TOTP(secret)
        return totp.now()

# Initialize TOTP manager
totp_manager = WebTOTPManager("MyAwesomeApp")

@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate-setup', methods=['POST'])
def generate_setup():
    """Generate TOTP setup"""
    try:
        # Dalam aplikasi nyata, account_name bisa diambil dari session/JWT
        account_name = "user@example.com"
        
        setup_data = totp_manager.generate_setup(account_name)
        
        return jsonify({
            'success': True,
            'secret': setup_data['secret'],
            'qr_code': setup_data['qr_code']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify TOTP token"""
    try:
        data = request.get_json()
        secret = data.get('secret')
        token = data.get('token')
        
        if not secret or not token:
            return jsonify({'success': False, 'error': 'Secret dan token required'}), 400
        
        is_valid = totp_manager.verify_token(secret, token)
        
        return jsonify({
            'success': True,
            'valid': is_valid
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/current-token', methods=['POST'])
def current_token():
    """Get current TOTP token"""
    try:
        data = request.get_json()
        secret = data.get('secret')
        
        if not secret:
            return jsonify({'success': False, 'error': 'Secret required'}), 400
        
        token = totp_manager.get_current_token(secret)
        
        return jsonify({
            'success': True,
            'token': token
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting TOTP Web Demo...")
    print("📱 Open browser: http://localhost:5000")
    print("🔐 Generate QR code dan scan dengan MFA app!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
