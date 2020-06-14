import socket, types, threading, time, datetime

from .Message import Message
from Utilities.FlushPrint import ptf

class TwitchWebsocket(threading.Thread):
    def __init__(self, host, port, chan, nick, auth, callback, capability = None, live = False):
        assert type(host) == str and type(port) == int and (type(callback) == types.FunctionType or type(callback) == types.MethodType)
        threading.Thread.__init__(self)
        self.name = "TwitchWebsocket"
        self._stop_event = threading.Event()

        # Variables
        self.host = host
        self.port = port
        self.chan = chan
        self.nick = nick
        self.auth = auth
        self.live = live
        self.callback = callback
        self.capability = capability

        self.data = str()

        # Lambda Functions.
        self.send_join = lambda message,    command="JOIN ": self._send(command, message)
        self.send_pong = lambda message="", command="PONG ": self._send(command, message)
        self.send_ping = lambda message="", command="PING ": self._send(command, message)
        self.send_nick = lambda message,    command="NICK ": self._send(command, message)
        self.send_pass = lambda message,    command="PASS ": self._send(command, message)
        self.send_part = lambda message,    command="PART ": self._send(command, message)
        self.send_req  = lambda message,    command="CAP REQ :twitch.tv/": self._send(command, message)
        self.send_message = lambda message, command="PRIVMSG ": self._send("{}{} :".format(command, self.chan.lower()), message) if self.live else print(message)
        self.send_whisper = lambda sender,  message: self.send_message(f"/w {sender} {message}")

    def start_nonblocking(self):
        self._initialize_websocket()
        self.start()
        self.login(self.nick, self.auth)
        self.join_channel(self.chan)

        if self.capability is not None:
            self.add_capability(self.capability)

    def start_bot(self):
        try:
            # Seting up the initial socket connection.
            self.start_nonblocking()

            # Loop to ensure that the try except is still active
            while not self.stopped():
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.join()

    def stop(self):
        self._stop_event.set()

    def join(self):
        # Stop the while loop in run()
        self.stop()
        # Cancel the self.conn.recv() in run()
        self.conn.shutdown(socket.SHUT_WR)
        # Join this thread
        threading.Thread.join(self)

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while not self.stopped():
            try:
                currentTime = datetime.datetime.now()
                if (currentTime - self.lastPingTime).total_seconds() > 330:
                    ptf("No PING. Reconnecting", time=True)
                    self.conn.shutdown(socket.SHUT_WR)

                    self._initialize_websocket()

                    if len(self.nick) > 0:
                        self.login(self.nick, self.auth)

                    if len(self.chan) > 1:
                        self.join_channel(self.chan)

                    if self.capability is not None:
                        self.add_capability(self.capability)

                try:
                    # Receive data from Twitch Websocket.
                    packet = self.conn.recv(8192).decode('UTF-8')
                except UnicodeDecodeError:
                    ptf("Received bad packet", time=True)
                    # In case of unexpected end of data.
                    continue


                self.data += packet
                data_split = self.data.split("\r\n")
                self.data = data_split.pop()

                # Iterate over seperately sent data.
                for line in data_split:
                    m = Message(line)

                    # We will do some handling depending on the message ourself,
                    # so the developer doesn't have to.
                    if m.type == "PING":
                        self.send_pong()

                    self.callback(m)

            except OSError as e:
                ptf(f"OSError: {e} -> {line}", time=True)

                self._initialize_websocket()

                if len(self.nick) > 0:
                    self.login(self.nick, self.auth)

                if len(self.chan) > 1:
                    self.join_channel(self.chan)

                if self.capability is not None:
                    self.add_capability(self.capability)

    def _send(self, command, message):
        if (sent := self.conn.send(bytes("{}{}\r\n".format(command, message), 'UTF-8'))) == 0:
            ptf("Socket connection broken, sent is 0", time=True)
            raise RuntimeError("Socket connection broken, sent is 0")

    def _initialize_websocket(self):
        while True:
            try:
                self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # We set the timeout to 330 seconds, as the PING from the Twitch server indicating
                # That the connection is still live is sent roughly every 5 minutes it seems.
                # the extra 30 seconds prevents us from checking the connection when it's not
                # needed.

                #TODO Error handle socket.gaierror: [Errno 11001] getaddrinfo failed and other errors
                self.conn.settimeout(330)

                self.conn.connect( (self.host, self.port) )
                self.lastPingTime = datetime.datetime.now()

                return
            except socket.gaierror:
                # Sleep and retry if not successful
                ptf("Failed to connect socket. Sleeping and retrying...", time=True)
                time.sleep(5)

    def join_channel(self, chan):
        assert type(chan) == str and len(chan) > 0

        self.chan = chan if chan[0] == "#" else "#" + chan
        self.send_join(self.chan.lower())

    def leave(self):
        self.send_part(self.chan.lower())

    def login(self, nick, auth):
        assert type(nick) == type(auth) == str

        self.nick = nick
        self.auth = auth
        self.send_pass(self.auth)
        self.send_nick(self.nick.lower())

    def add_capability(self, capability):
        assert type(capability) in [list, str]

        self.capability = capability

        if type(capability) == list:
            for cap in capability:
                self.send_req(cap.lower())
        else:
            self.send_req(capability.lower())

        ptf("")
        ptf("Connected to Twitch IRC\n", time=True)
