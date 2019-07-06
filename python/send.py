#
# pip install pynacl
# pip install websocket_client
#

import argparse
import hashlib
import json
import ssl
import random
import time
import websocket
import nacl.encoding
import nacl.signing
from collections import OrderedDict

GENESIS_BLOCK_ID = "00000000e29a7850088d660489b7b9ae2da763bc3bd83324ecc54eee04840adb"

# from constants.go
CRUZBITS_PER_CRUZ = 100000000

BLOCKS_UNTIL_NEW_SERIES = 1008

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-sender",
                    help="base64 encoded private key of the sender",
                    type=str)
parser.add_argument("-recipient",
                    help="base64 encoded public key of the recipient",
                    type=str)
parser.add_argument("-amount", help="amount to send in cruzbits", type=int)
parser.add_argument("--fee",
                    help="transaction fee to pay in cruzbits",
                    type=int,
                    default=int(0.01 * CRUZBITS_PER_CRUZ),
                    required=False)
parser.add_argument("--memo",
                    help="an optional memo to include",
                    type=str,
                    default="",
                    required=False)
parser.add_argument("--peer",
                    help="address of our client peer",
                    type=str,
                    default="127.0.0.1:8831",
                    required=False)
args = parser.parse_args()

# decode the sender private key
sender_private_key = nacl.signing.SigningKey(
    args.sender, encoder=nacl.encoding.Base64Encoder)

# this is what will go in the transaction's "from" field
sender_public_key = sender_private_key.verify_key.encode(
    encoder=nacl.encoding.Base64Encoder).decode("utf-8")

# connect to our peer
ws = websocket.create_connection("wss://" + args.peer + "/" + GENESIS_BLOCK_ID,
                                 subprotocols=["cruzbit.1"],
                                 sslopt={
                                     "cert_reqs": ssl.CERT_NONE,
                                     "check_hostname": False
                                 })
ws.send(json.dumps({"type": "get_tip_header"}))

tx_hash = None
while True:
    msg = json.loads(ws.recv())

    if msg["type"] == "tip_header":
        # record the current height
        height = msg['body']['header']['height']

        # create the transaction
        transaction = [
            ("time", int(time.time())),
            ("nonce", random.randint(0, 2**31 - 1)),
            ("from", sender_public_key),
            ("to", args.recipient),
            ("amount", args.amount),
            ("fee", args.fee),
            ("memo", args.memo),
            ("expires", height + 3),  # must be mined within the next 3 blocks
            ("series", int(height / BLOCKS_UNTIL_NEW_SERIES) + 1),
        ]

        tx = OrderedDict(transaction)
        if args.fee <= 0:
            del tx["fee"]
        if len(args.memo) == 0:
            del tx["memo"]

        # compute the hash
        h = hashlib.new("sha3_256")
        h.update(json.dumps(tx, separators=(",", ":")).encode("utf-8"))
        tx_hash = h.digest()

        # sign it
        signed_message = sender_private_key.sign(
            tx_hash, encoder=nacl.encoding.Base64Encoder)
        transaction.append(
            ("signature", signed_message.signature.decode("utf-8")))
        signed_tx = OrderedDict(transaction)

        # send the transaction
        ws.send(
            json.dumps({
                "type": "push_transaction",
                "body": {
                    "transaction": signed_tx
                }
            }))

    if msg["type"] == "push_transaction_result":
        # display the response
        print(msg["body"].get("error",
                              "Transaction " + tx_hash.hex() + " sent"))
        ws.close()
        break
