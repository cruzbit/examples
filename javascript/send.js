//
// npm install argparse
// npm install websocket
// npm install tweetnacl
// npm install tweetnacl-util
//

const ArgParser = require("argparse").ArgumentParser;
const WebSocket = require("websocket").client;
const nacl = require("tweetnacl");
const util = require("tweetnacl-util");
const {SHA3} = require('sha3');

const GENESIS_BLOCK_ID = "00000000e29a7850088d660489b7b9ae2da763bc3bd83324ecc54eee04840adb"

// from constants.go
const CRUZBITS_PER_CRUZ = 100000000

const BLOCKS_UNTIL_NEW_SERIES = 1008

// parse arguments
const parser = new ArgParser({
  addHelp: true,
  description: "send cruzbits"
});
parser.addArgument(["--sender"], {
  help: "base64 encoded private key"
});
parser.addArgument(["--recipient"], {
  help: "base64 encoded public key"
});
parser.addArgument(["--amount"], {
  help: "amount in cruzbits",
  type: "int"
});
parser.addArgument(["--fee"], {
  help: "fee in cruzbits",
  type: "int",
  defaultValue: Math.floor(0.01 * CRUZBITS_PER_CRUZ)
});
parser.addArgument(["--memo"], {
  help: "optional memo",
  defaultValue: ""
});
parser.addArgument(["--peer"], {
  help: "host:port",
  defaultValue: "127.0.0.1:8831"
});

const args = parser.parseArgs();

const senderPrivateKey = nacl.sign.keyPair.fromSecretKey(util.decodeBase64(args.sender));

const ws = new WebSocket();

ws.on("connectFailed", function(error) {
  console.log(error.toString());
});

tx_hash = null;
ws.on("connect", function(conn) {
  conn.on("message", function(message) {
    if (message.type !== "utf8") {
      return;
    }

    msg = JSON.parse(message.utf8Data);
    switch (msg.type) {
      case "tip_header":
        // record the height
        height = msg.body.header.height;

        // create the transaction
        transaction = {
          time: Math.floor(Date.now() / 1000),
          nonce: Math.floor(Math.random() * (2 ** 31 - 1)),
          from: util.encodeBase64(senderPrivateKey.publicKey),
          to: args.recipient,
          amount: args.amount,
          fee: args.fee,
          memo: args.memo,
          expires: height + 3, // must be mined within the next 3 blocks
          series: Math.floor(height / BLOCKS_UNTIL_NEW_SERIES) + 1,
        }
        if (transaction.fee === 0) {
          delete transaction.fee;
        }
        if (transaction.memo.length === 0) {
          delete transaction.memo;
        }

        // compute the hash
        const h = new SHA3(256);
        h.update(JSON.stringify(transaction));
        tx_hash = h.digest();

        // sign it
        transaction["signature"] = util.encodeBase64(nacl.sign.detached(tx_hash, senderPrivateKey.secretKey));

        // send the transaction
        conn.sendUTF(JSON.stringify({
          type: "push_transaction",
          body: {
            transaction: transaction
          }
        }));
        break;

      case "push_transaction_result":
        // display the response
        if ("error" in msg.body) {
          console.log(msg.body.error);
        } else {
          console.log("Transaction " + tx_hash.toString("hex") + " sent");
        }
        conn.close();
        process.exit();
    }
  });

  conn.sendUTF(JSON.stringify({
    type: "get_tip_header"
  }));
});

// connect to our peer
ws.connect("wss://" + args.peer + "/" + GENESIS_BLOCK_ID, null, null, null, {
  rejectUnauthorized: false
});
