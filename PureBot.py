from TwitchWebsocket import TwitchWebsocket

class PureBot:
    def message_handler(self, m):
            try:
                if m.type == "366":
                    #print(f"Successfully joined channel: #{m.channel}")
                    pass

                elif m.type == "NOTICE":
                    #print(m.message)
                    pass

                elif m.type == "PRIVMSG":
                    # Look for commands.
                    if m.message.startswith("!average") and self.check_permissions(m) and self.check_timeout():
                        self.command_average(m)
                    elif m.message.startswith("!vote") and self.check_permissions(m) and self.check_timeout():
                        self.command_vote(m)
                    else:
                        # Parse message for potential numbers/votes and emotes.
                        self.check_for_numbers(m.message, m.user)
                        self.check_for_text(m.message, m.user)
                        self.check_for_emotes(m)

            except Exception as e:
                logging.error(e)

    self.socket = TwitchWebsocket(host="irc.chat.twitch.tv",
                                  port=6667,
                                  chan="#PureSushi",
                                  nick="puresushibot",
                                  auth="oauth",
                                  callback=message_handler,
                                  capability=["tags"],
                                  live=False)
