# Copyright 2019 cruzbit developers
# Use of this source code is governed by a MIT-style license that can be found in the LICENSE file.
#
# gem install ed25519
#

require "base64"
require "ed25519"

# generate a new key pair
key = Ed25519::SigningKey.generate

# base64 encode them
private_key = Base64.strict_encode64(key.to_bytes)
public_key = Base64.strict_encode64(key.verify_key.to_bytes)

puts "private key: " + private_key
puts "public key: " + public_key
