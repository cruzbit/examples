# Copyright 2019 cruzbit developers
# Use of this source code is governed by a MIT-style license that can be found in the LICENSE file.
#
# pip install websocket_client
#

import argparse
import json
import ssl
import websocket

GENESIS_BLOCK_ID = "00000000e29a7850088d660489b7b9ae2da763bc3bd83324ecc54eee04840adb"

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-pubkey",
                    help="base64 encoded public key whose balance to retrieve",
                    type=str)
parser.add_argument("--peer",
                    help="address of our client peer",
                    type=str,
                    default="127.0.0.1:8831",
                    required=False)
args = parser.parse_args()

# connect to our peer
ws = websocket.create_connection("wss://" + args.peer + "/" + GENESIS_BLOCK_ID,
                                 subprotocols=["cruzbit.1"],
                                 sslopt={
                                     "cert_reqs": ssl.CERT_NONE,
                                     "check_hostname": False
                                 })

# request the balance
ws.send(
    json.dumps({
        "type": "get_balance",
        "body": {
            "public_key": args.pubkey
        }
    }))

while True:
    msg = json.loads(ws.recv())

    if msg["type"] == "balance":
        if msg["body"].get("error"):
            print(msg["body"].get("error"))
        else:
            print("{0} balance is {1} as of block height {2}".format(
                args.pubkey, msg["body"]["balance"], msg["body"]["height"]))
        ws.close()
        break
