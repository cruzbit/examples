#
# pip install pynacl
#

import nacl.encoding
import nacl.signing

# generate a new key pair
key = nacl.signing.SigningKey.generate()

# base64 encode them
private_key = key.encode(encoder=nacl.encoding.Base64Encoder).decode("utf-8")
public_key = key.verify_key.encode(
    encoder=nacl.encoding.Base64Encoder).decode("utf-8")

print("private key: " + private_key)
print("public key: " + public_key)
