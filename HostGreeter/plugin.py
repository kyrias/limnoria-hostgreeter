###
# Copyright (c) 2019, Johannes Löthberg
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

from supybot import utils, plugins, dbi, ircutils, callbacks, ircmsgs, ircdb
from supybot.commands import *


class DbiHostGreeterDB(dbi.DB):
    class Record(dbi.Record):
        __fields__ = ['channel', 'hostmask', 'greeting']

        def __str__(self):
            return '{}: {!r}'.format(self.hostmask, self.greeting)

        def __repr__(self):
            return '<HostGreeterEntry channel={!r} hostmask={!r} greeting={!r}'.format(self.channel, self.hostmask, self.greeting)


    def __init__(self, filename):
        self.__parent = super(self.__class__, self)
        self.__parent.__init__(filename)

    def add(self, channel, hostmask, greeting):
        return self.__parent.add(
                self.Record(channel=channel, hostmask=hostmask, greeting=greeting))

HostGreeterDB = plugins.DB('HostGreeter', {'flat': DbiHostGreeterDB})


class HostGreeter(callbacks.Plugin):
    """Greet users based on hostmask"""

    def __init__(self, irc):
        self.__parent = super(HostGreeter, self)
        self.__parent.__init__(irc)
        self.db = HostGreeterDB()


    def die(self):
        self.db.close()
        self.__parent.die()


    def list(self, irc, msg, args, channel):
        """<channel>"""

        entries = [str(entry) for entry in self.db if entry.channel == channel]
        irc.reply(utils.str.commaAndify(entries))

    list = wrap(list, ['channel'])


    def get(self, irc, msg, args, channel, hostmask):
        """<channel> <hostmask>"""

        def predicate(entry):
            return entry.channel == channel and \
                    ircutils.hostmaskPatternEqual(entry.hostmask, hostmask)

        entries = [str(entry) for entry in self.db.select(predicate)]
        irc.reply(utils.str.commaAndify(entries))

    get = wrap(get, ['channel', 'hostmask'])


    def add(self, irc, msg, args, channel, hostmask, greeting):
        """<channel> <hostmask> <greeting>"""

        def predicate(entry):
            return entry.channel == channel and entry.hostmask == hostmask

        for entry in self.db.select(predicate):
            self.db.remove(entry.id)

        self.db.add(channel, hostmask, greeting)
        irc.replySuccess()

    add = wrap(add, ['channel', 'hostmask', 'text'])


    def remove(self, irc, msg, args, channel, hostmask):
        """<channel> <hostmask>"""

        def predicate(entry):
            return entry.channel == channel and entry.hostmask == hostmask

        entry = next(self.db.select(predicate), None)
        if not entry:
            irc.reply('No greeting with that hostmask found')
            return

        self.db.remove(entry.id)
        irc.replySuccess()

    remove = wrap(remove, ['channel', 'hostmask'])


    def doJoin(self, irc, msg):
        def predicate(entry):
            return entry.channel == msg.args[0] and \
                    ircutils.hostmaskPatternEqual(entry.hostmask, msg.prefix)
        entry = next(self.db.select(predicate), None)
        if entry:
            irc.reply(entry.greeting)
        else:
            irc.noReply()


Class = HostGreeter

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
