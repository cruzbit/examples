#
# gem install eventmachine
# gem install faye-websocket
#

require "eventmachine"
require "faye/websocket"
require "json"
require "optparse"

GENESIS_BLOCK_ID = "00000000e29a7850088d660489b7b9ae2da763bc3bd83324ecc54eee04840adb"

# parse arguments
options = { peer: "127.0.0.1:8831" }
OptionParser.new do |opt|
  opt.on("--pubkey <base64 encoded public key>") { |o| options[:pubkey] = o }
  opt.on("--peer <host:port>") { |o| options[:peer] = o }
end.parse!

EM.run {
  # connect to our peer
  ws = Faye::WebSocket::Client.new("wss://" + options[:peer] + "/" + GENESIS_BLOCK_ID)

  ws.on :open do |event|
    # request the balance
    ws.send({ type: "get_balance", body: { public_key: options[:pubkey] } }.to_json)
  end

  ws.on :message do |event|
    msg = JSON.parse(event.data)
    case msg["type"]
    when "balance"
      puts options[:pubkey] + " balance is " + msg["body"]["balance"].to_s + " as of block height " + msg["body"]["height"].to_s
      exit
    end
  end

  ws.on :close do |event|
    raise "exiting, code: " + event.code.to_s + ", reason: " + event.reason
  end
}
