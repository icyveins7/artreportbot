#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 13 19:18:41 2021

@author: seolubuntu
"""

from bot_commonHandlers import CommonBot
from dataclasses import dataclass
import datetime as dt
from telegram.ext import CommandHandler, CallbackContext
import telegram
import sys

#%% Data structs
@dataclass
class Submission:
    name: str
    lastsubmit: dt.datetime # in UTC
    
weekdayStrings = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}

#%%
class ARTBot(CommonBot):
    def __init__(self, cutday = 1, cuthour = 23, cutmin = 59,
                 startday = 1, starthour = 0, startmin = 1,
                 reminderTimes = []):
        super().__init__()
        
        # Storage dict for submissions
        self.store = {}
        # Storage dict for channels
        self.channel = None
        
        # Parameters
        self.cutday = cutday # Monday is 0, Sunday is 6.
        self.cuthour = cuthour
        self.cutmin = cutmin
        
        self.startday = startday
        self.starthour = starthour
        self.startmin = startmin
        
        self.open = False # True: is currently open for submits, False: downtime
        
        # Initialize submission windows
        self.setNextWindow()
        
        # Add reminder times (tuples of (weekday, hr, min))
        self.reminderTimes = reminderTimes
        
        # Start jobs
        self.updater.job_queue.run_repeating(self.minutely_job, interval=10, first=0)
        
        print("ARTBot init'ed.")
        
    def addHandlers(self):
        super().addHandlers()
        
        self.dispatcher.add_handler(CommandHandler('submit', self.submit))
        self.dispatcher.add_handler(CommandHandler('name', self.name))
        self.dispatcher.add_handler(CommandHandler('announce', self.announce))
        self.dispatcher.add_handler(CommandHandler('reminders', self.reminders))
        self.dispatcher.add_handler(CommandHandler('report', self.report))
        self.dispatcher.add_handler(CommandHandler('reportfull', self.reportfull))
        self.dispatcher.add_handler(CommandHandler('start', self.start))
        
        print("Added ARTBot's handlers.")
        
    def setNextWindow(self):
        self.openStart = self.getRelativeNextDatetime(self.startday, self.starthour, self.startmin)
        self.openEnd = self.getRelativeNextDatetime(self.cutday, self.cuthour, self.cutmin)
        
        print("Next window is from %s to %s" % (self.openStart, self.openEnd))
        
    def getRelativeNextDatetime(self, day, hour, minute):
        now = dt.datetime.now()
        d = 0 # counter for days
        
        while (True):
            if (now.weekday() + d) % 7 == day:
                break
            else:
                d = d + 1
                
        target = now + dt.timedelta(days=d)
        target = target.replace(hour=hour, minute=minute)
        
        return target
        
    #%% Commands
    def submit(self, update, context):
        user = update.message.from_user
        
        now = dt.datetime.now()
        
        # Update internal history
        if user.id in self.store.keys():
            self.store[user.id].lastsubmit = now
            print("Updating %s timing to %s" % (user.id, now))
            context.bot.send_message(chat_id = update.message.chat_id,
                                     text = "(%d) %s: Submit received!" % (user.id, self.store[user.id].name))
            
        else:
            context.bot.send_message(chat_id = update.message.chat_id, text="Please register first with /name. E.g. /name Low Chun Wah Edwin")
        
        
        # Debug print
        print(self.store[user.id])
        
        
    def name(self, update, context):
        user = update.message.from_user
        
        if len(context.args) == 0:
            context.bot.send_message(chat_id = update.message.chat_id,
                                     text = "Please type the command like this; e.g. /name Low Chun Wah Edwin")
        
        # Update internal name
        elif user.id in self.store.keys():
            self.store[user.id].name = ' '.join(context.args)
            print("Updated %s name to %s" % (user.id, self.store[user.id].name))
            context.bot.send_message(chat_id = update.message.chat_id,
                                     text = "(%d) %s: Changed name!" % (user.id, self.store[user.id].name))
        else:
            self.store[user.id] = Submission(' '.join(context.args), None)
            context.bot.send_message(chat_id = update.message.chat_id,
                                     text = "%s has been added to the list. If you'd like direct message reminders as well, please just open a conversation with me via https://telegram.me/%s" % (self.store[user.id].name, context.bot.username))
            
    def announce(self, update, context):
        self.channel = update.message.chat_id
        
        context.bot.send_message(chat_id = self.channel,
                                 text = "Submission window is from %s to %s." % (self.openStart, self.openEnd))
            
    def reminders(self, update, context):
        txt = 'Reminders will be sent at the following times:\n'
        timings = ["%s, %2d:%2d\n" % (weekdayStrings[i[0]],i[1],i[2]) for i in self.reminderTimes]
        timings.insert(0, txt)
        context.bot.send_message(chat_id = update.message.chat_id,
                                 text = ''.join(timings))
        
    def report(self, update, context):
        txt = "Not submitted this window:\n"
        for key, val in self.store.items():
            if val.lastsubmit is None:
                txt = txt + "%s\n" % val.name
        
        context.bot.send_message(chat_id = update.message.chat_id,
                                 text = txt)
        
    def reportfull(self, update, context):
        self.report(update,context)
        txt = "Submitted this window:\n"
        for key, val in self.store.items():
            if val.lastsubmit is not None:
                txt = txt + "%s\n" % val.name
                
        context.bot.send_message(chat_id = update.message.chat_id,
                                 text = txt)
        
    def start(self, update, context):
        context.bot.send_message(chat_id = update.message.from_user.id,
                                 text = "You're all set, you will receive direct message reminders here!")
        
    #%% Jobs
    def minutely_job(self, context: CallbackContext):
        # State changes for submission window
        now = dt.datetime.now()
        if not self.open and now > self.openStart:
            print("Opening submission window!")
            context.bot.send_message(chat_id = self.channel,
                                     text = "Submission window has opened.")
            self.open = True
        if self.open and now > self.openEnd:
            print("Closing submission window!")
            
            context.bot.send_message(chat_id = self.channel,
                                     text = "Submission window has closed.")
            self.open = False
            self.setNextWindow()
            for key, val in self.store.items():
                val.lastsubmit = None # reset all submission times to None
            
        # Exact time reminders
        userlist = []
        if (now.weekday(),now.hour,now.minute) in self.reminderTimes:
            for userid in self.store.keys():
                if self.store[userid].lastsubmit is None:
                    try:
                        print("Timed reminder for user %s" % userid)
                        userlist.append(userid)
                        context.bot.send_message(chat_id = userid,
                                                 text = "Reminder to update your ART!")
                    except:
                        print("Failed to send DM to user %s:%s" % (userid, self.store[userid].name))
                
            channeltext = "Reminder to update your ARTS:\n"
            for i in userlist:
                mention = "["+self.store[i].name+"](tg://user?id="+str(i)+")"
                channeltext = channeltext + mention + "\n"
            
            if self.channel is not None:
                context.bot.send_message(chat_id = self.channel,
                                         text = channeltext,
                                         parse_mode = telegram.ParseMode.MARKDOWN_V2)
        
        
#%%
if __name__ == "__main__":
    reminderTimes = []
    
    if len(sys.argv) > 1 and sys.argv[1] == 'debug':
        # Debug reminderTimes
        now = dt.datetime.now()
        later = now + dt.timedelta(minutes=1)
        later2 = later + dt.timedelta(minutes=1)
        later3 = later2 + dt.timedelta(minutes=1)
        laterhr = later + dt.timedelta(hours=1)
        reminderTimes.append((later.weekday(), later.hour, later.minute))
        print("Debug mode, setting reminder times to shortly after now..")
        artbot = ARTBot(cutday = later2.weekday(), cuthour = later2.hour, cutmin = later2.minute,
                         startday = later.weekday(), starthour = later.hour, startmin = later.minute,
                         reminderTimes = reminderTimes)
        artbot.run()
        
    else:
        # Default reminderTimes
        reminderTimes.append((1,7,0))
        reminderTimes.append((1,8,0))
        reminderTimes.append((1,21,0))
        reminderTimes.append((1,22,0))
        reminderTimes.append((1,23,0))
        reminderTimes.append((1,23,30))
    
        artbot = ARTBot(reminderTimes = reminderTimes)
        artbot.run()