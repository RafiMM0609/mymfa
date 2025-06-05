import pyotp
import qrcode
import secrets
import io
import base64
from PIL import Image

class TOTPGenerator:
    def __init__(self, service_name="MyApp", account_name=None):
        """
        Initialize TOTP Generator
        
        Args:
            service_name (str): Nama aplikasi/service Anda
            account_name (str): Nama akun user (email/username)
        """
        self.service_name = service_name
        self.account_name = account_name or "user@example.com"
        
    def generate_secret(self):
        """Generate secret key yang aman untuk TOTP"""
        # Generate 32 byte random secret dan encode ke base32
        return pyotp.random_base32()
    
    def create_totp_instance(self, secret):
        """
        Buat instance TOTP dengan secret key
        
        Args:
            secret (str): Base32 encoded secret key
            
        Returns:
            pyotp.TOTP: Instance TOTP
        """
        return pyotp.TOTP(secret)
    
    def generate_provisioning_uri(self, secret):
        """
        Generate provisioning URI untuk QR code
        
        Args:
            secret (str): Base32 encoded secret key
            
        Returns:
            str: Provisioning URI
        """
        totp = self.create_totp_instance(secret)
        
        # Format URI yang kompatibel dengan Google Authenticator, Authy, dll
        return totp.provisioning_uri(
            name=self.account_name,
            issuer_name=self.service_name
        )
    
    def generate_qr_code(self, secret, save_path=None):
        """
        Generate QR code untuk TOTP setup
        
        Args:
            secret (str): Base32 encoded secret key
            save_path (str, optional): Path untuk save QR code image
            
        Returns:
            PIL.Image: QR code image
        """
        # Get provisioning URI
        provisioning_uri = self.generate_provisioning_uri(secret)
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save jika path diberikan
        if save_path:
            img.save(save_path)
            print(f"QR code saved to: {save_path}")
        
        return img
    
    def get_current_token(self, secret):
        """
        Get current TOTP token
        
        Args:
            secret (str): Base32 encoded secret key
            
        Returns:
            str: Current 6-digit TOTP token
        """
        totp = self.create_totp_instance(secret)
        return totp.now()
    
    def verify_token(self, secret, token):
        """
        Verify TOTP token
        
        Args:
            secret (str): Base32 encoded secret key
            token (str): 6-digit token untuk diverifikasi
            
        Returns:
            bool: True jika token valid
        """
        totp = self.create_totp_instance(secret)
        return totp.verify(token)

def demo_totp_setup():
    """Demo lengkap setup TOTP dengan QR code"""
    
    print("=== TOTP Generator Demo ===\n")
    
    # Inisialisasi generator
    generator = TOTPGenerator(
        service_name="MyAwesomeApp",
        account_name="user@example.com"
    )
    
    # 1. Generate secret key
    secret = generator.generate_secret()
    print(f"1. Generated Secret Key: {secret}")
    print("   (Simpan secret ini dengan aman di database)\n")
    
    # 2. Generate provisioning URI
    uri = generator.generate_provisioning_uri(secret)
    print(f"2. Provisioning URI: {uri}\n")
    
    # 3. Generate QR Code
    print("3. Generating QR Code...")
    qr_image = generator.generate_qr_code(secret, "totp_qrcode.png")
    print("   QR Code generated! Check 'totp_qrcode.png'\n")
    
    # 4. Show QR code di terminal (ASCII art)
    qr_text = qrcode.QRCode()
    qr_text.add_data(uri)
    qr_text.make()
    qr_text.print_ascii()
    
    print("\n4. Scan QR code dengan aplikasi MFA seperti:")
    print("   - Google Authenticator")
    print("   - Microsoft Authenticator") 
    print("   - Authy")
    print("   - 1Password")
    print("   - Bitwarden\n")
    
    # 5. Demo verifikasi
    print("5. Demo verifikasi token:")
    current_token = generator.get_current_token(secret)
    print(f"   Current token: {current_token}")
    
    # Verifikasi token yang baru dibuat
    is_valid = generator.verify_token(secret, current_token)
    print(f"   Token valid: {is_valid}")
    
    return secret, generator

if __name__ == "__main__":
    # Jalankan demo
    secret_key, totp_gen = demo_totp_setup()
    
    print(f"\n=== Setup Complete ===")
    print(f"Secret Key: {secret_key}")
    print("Save secret key ini untuk verifikasi token nantinya!")
