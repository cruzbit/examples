# Copyright 2019 cruzbit developers
# Use of this source code is governed by a MIT-style license that can be found in the LICENSE file.
#
# gem install ed25519
# gem install sha3
# gem install eventmachine
# gem install faye-websocket
#

require "base64"
require "ed25519"
require "eventmachine"
require "faye/websocket"
require "json"
require "optparse"
require "sha3"

GENESIS_BLOCK_ID = "00000000e29a7850088d660489b7b9ae2da763bc3bd83324ecc54eee04840adb"

# from constants.go
CRUZBITS_PER_CRUZ = 100000000

BLOCKS_UNTIL_NEW_SERIES = 1008

# parse arguments
options = { peer: "127.0.0.1:8831", fee: (0.01 * CRUZBITS_PER_CRUZ).to_i }
OptionParser.new do |opt|
  opt.on("--sender <base64 encoded private key>") { |o| options[:sender_private_key] = Ed25519::SigningKey.new(Base64.decode64(o)) }
  opt.on("--recipient <base64 encoded public key>") { |o| options[:recipient] = o }
  opt.on("--amount <amount in cruzbits>") { |o| options[:amount] = o.to_i }
  opt.on("--fee <fee in cruzbits>") { |o| options[:fee] = o.to_i }
  opt.on("--memo <optional memo>") { |o| options[:memo] = o }
  opt.on("--peer <host:port>") { |o| options[:peer] = o }
end.parse!

tx_hash = nil
EM.run {
  # connect to our peer
  ws = Faye::WebSocket::Client.new("wss://" + options[:peer] + "/" + GENESIS_BLOCK_ID)

  ws.on :open do |event|
    ws.send({ type: "get_tip_header" }.to_json)
  end

  ws.on :message do |event|
    msg = JSON.parse(event.data)
    case msg["type"]
    when "tip_header"
      # record the current height
      height = msg["body"]["header"]["height"]

      # create the transaction
      transaction = {
        time: Time.now.to_i,
        nonce: Random.rand(2 ** 31 - 1),
        from: Base64.strict_encode64(options[:sender_private_key].verify_key),
        to: options[:recipient],
        amount: options[:amount],
        fee: options[:fee],
        memo: options[:memo],
        expires: height + 3, # must be mined within the next 3 blocks
        series: (height / BLOCKS_UNTIL_NEW_SERIES).to_i + 1,
      }
      if options[:fee] == 0
        transaction.delete :fee
      end
      if options[:memo] == nil
        transaction.delete :memo
      end

      # compute the hash
      h = SHA3::Digest::SHA256.new
      h << transaction.to_json
      tx_hash = h.digest

      # sign it
      transaction[:signature] = Base64.strict_encode64(options[:sender_private_key].sign(tx_hash))

      # send the transaction
      ws.send({ type: "push_transaction", body: { transaction: transaction } }.to_json)

    when "push_transaction_result"
      # display the response
      if msg["body"]["error"] != nil
        puts msg["body"]["error"]
      else
        puts "Transaction " + tx_hash.unpack("H*").first + " sent"
      end
      exit
    end
  end

  ws.on :close do |event|
    raise "exiting, code: " + event.code.to_s + ", reason: " + event.reason
  end
}
