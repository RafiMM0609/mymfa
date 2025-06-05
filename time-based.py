import pyotp
import time

totp = pyotp.TOTP('base32secret3232')
token = totp.now() # => '492039'
print(token)

# OTP verified for current time
print(totp.verify(token)) # => True
time.sleep(30)
print(totp.verify(token)) # => False