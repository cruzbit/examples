//
// npm install argparse
// npm install websocket
//

const ArgParser = require("argparse").ArgumentParser;
const WebSocket = require("websocket").client;

const GENESIS_BLOCK_ID = "00000000e29a7850088d660489b7b9ae2da763bc3bd83324ecc54eee04840adb"

// parse arguments
const parser = new ArgParser({
  addHelp: true,
  description: "get public key balance"
});
parser.addArgument(["--pubkey"], {
  help: "base64 encoded public key"
});
parser.addArgument(["--peer"], {
  help: "host:port",
  defaultValue: "127.0.0.1:8831"
});

const args = parser.parseArgs();

const ws = new WebSocket();

ws.on("connectFailed", function(error) {
  console.log(error.toString());
});

ws.on("connect", function(conn) {
  conn.on("message", function(message) {
    if (message.type !== "utf8") {
      return;
    }
    msg = JSON.parse(message.utf8Data);
    switch (msg.type) {
      case "balance":
        console.log(msg.body.public_key + " balance is " + msg.body.balance +
          " as of block height " + msg.body.height);
        conn.close();
        process.exit();
    }
  });

  // request the balance
  conn.sendUTF(JSON.stringify({
    type: "get_balance",
    body: {
      public_key: args.pubkey
    }
  }));
});

// connect to our peer
ws.connect("wss://" + args.peer + "/" + GENESIS_BLOCK_ID, null, null, null, {
  rejectUnauthorized: false
});
