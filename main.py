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

#%% Data structs
@dataclass
class Submission:
    name: str
    lastsubmit: dt.datetime # in UTC

#%%
class ARTBot(CommonBot):
    def __init__(self):
        super().__init__()
        
        # Storage dict for submissions
        self.store = {}
        
        # Parameters
        self.cutday = 1 # Monday is 0, Sunday is 6.
        self.cuthour = 23
        self.cutmin = 59
        
        # Start jobs
        self.updater.job_queue.run_repeating(self.remind_job, interval=5, first=0)
        
        print("ARTBot init'ed.")
        
    def addHandlers(self):
        super().addHandlers()
        
        self.dispatcher.add_handler(CommandHandler('submit', self.submit))
        self.dispatcher.add_handler(CommandHandler('name', self.name))
        
        print("Added ARTBot's handlers.")
        
    def submit(self, update, context):
        user = update.message.from_user
        
        now = dt.datetime.utcnow()
        
        # Update internal history
        if user.id in self.store.keys():
            self.store[user.id].lastsubmit = now
            print("Updating %s timing to %s" % (user.id, now))
            
        else:
            self.store[user.id] = Submission(user.first_name, now)
            print("Adding new user %s with timing %s" % (user.id, now))
            
        
        
        context.bot.send_message(chat_id = update.message.chat_id,
                                 text = "(%d) %s: Submit received!" % (user.id, self.store[user.id].name))
        
        # Debug print
        print(self.store[user.id])
        
        
    def name(self, update, context):
        user = update.message.from_user
        
        # Update internal name
        if user.id in self.store.keys():
            self.store[user.id].name = ' '.join(context.args)
            print("Updated %s name to %s" % (user.id, self.store[user.id].name))
            context.bot.send_message(chat_id = update.message.chat_id,
                                     text = "(%d) %s: Changed name!" % (user.id, self.store[user.id].name))
        else:
            context.bot.send_message(chat_id = update.message.chat_id,
                                     text = "(%d) %s: Please /submit at least once before changing name!" % (user.id, user.first_name))
        
    def remind_job(self, context: CallbackContext):
        if len(self.store.keys()) < 1:
            print("No users yet.")
        else:
            for userid in self.store.keys():
                print("Reminding user %s" % (userid))
                context.bot.send_message(chat_id = userid,
                                         text = "Reminder to update your ART!")
        
#%%
if __name__ == "__main__":
    artbot = ARTBot()
    artbot.run()