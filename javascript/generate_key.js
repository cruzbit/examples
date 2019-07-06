//
// npm install tweetnacl
// npm install tweetnacl-util
//

const nacl = require("tweetnacl");
const util = require("tweetnacl-util");

// generate a new key pair
key = nacl.sign.keyPair();

// base64 encode them
private_key = util.encodeBase64(key.secretKey);
public_key = util.encodeBase64(key.publicKey);

console.log("private key: " + private_key);
console.log("public key: " + public_key);
