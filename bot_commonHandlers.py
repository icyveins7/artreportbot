# -*- coding: utf-8 -*-
"""
Created on Thu Nov 26 11:28:16 2020

@author: Seo
"""


from telegram.ext import Updater, Filters, CommandHandler, MessageHandler, MessageFilter, CallbackQueryHandler, CallbackContext
import os
import ntpath
import pytz
import datetime as dt
import subprocess
import zipfile

#%% refactor as class to inherit
class CommonBot:
    def __init__(self, timezone=pytz.timezone('Singapore'), token=None):
        self.fileDir = ntpath.split(os.path.realpath(__file__))[0]
        
        self.tz = timezone
        
        self.time_bot_started = dt.datetime.now()
        self.time_bot_started = self.tz.localize(self.time_bot_started) # this is the correct way

        if token is None:
            self.token = os.environ['TELEGRAM_BOT_TOKEN'] # always use environ variables when you can, rather than files
        else:
            self.token = token
            
        # standard initializers
        self.updater = Updater(token=self.token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        
        # add common handlers
        self.addHandlers()
        
        print("Common Bot initializer complete.")
        

    #%% Generic Methods
    def run(self):
        print("Bot running..")
        self.updater.start_polling()
        self.updater.idle()
    
    def getLocalizedTimeNow(self):
        return self.tz.localize(dt.datetime.now())
    
    def checkCommandIsOld(self, message):
        print('Datetime message was received was '+str(message.date))
        print('Bot started at ' + str(time_bot_started))
        print('%20s : %s' % ('Message time', str(message.date.timestamp())))
        print('%20s : %s' % ('Bot start time', str(time_bot_started.timestamp())))
    
        if message.date.timestamp() <= time_bot_started.timestamp():
            print('old msg')
            return True
        else:
            print('new msg')
            return False
        
    
    def botShutdown(self):
        os._exit(0) # hardcore? but always works 
        # updater.stop()
        # updater.is_idle = False
    
    
    def botRestart(self):
        os._exit(1) # exit code is now 1
    
    
    def runScriptToFile(self, script, file):
        with open(file,"w+") as fid:
            subprocess.call(["python", script], stdout=fid)
    
    # file management
    def zipFiles(self, filepaths, zipfilepath, cl=9):
        '''Compression levels 0 (no compression) to 9 (max compression)'''
        z = zipfile.ZipFile(zipfilepath,'w', compression=zipfile.ZIP_DEFLATED, compresslevel=cl)
        
        for fp in filepaths:
            z.write(fp)
        
        z.close()
        
    
    #%% Handlers
    def status(self, update, context):
        if not self.checkCommandIsOld(update.message):
            timeNow = self.getLocalizedTimeNow()
            gitlogstr = subprocess.check_output(['git', 'log', '-1', '--oneline']).strip().decode('utf-8')
            context.bot.send_message(chat_id=update.message.chat_id,
                             text='This bot was started at '+str(self.time_bot_started)+' and has been alive for '+str(timeNow-time_bot_started))
            context.bot.send_message(chat_id=update.message.chat_id,
                             text=f'It is currently running off commit: {gitlogstr}')
    
    
    def stopBot(self, update, context):
        if not self.checkCommandIsOld(update.message):
            context.bot.send_message(chat_id=update.message.chat_id,
                                     text='Ending this bot.')
            print("Ending the bot.")
            # os.kill(os.getpid(), signal.SIGINT)
            # threading.Thread(target=botShutdown).start()
            self.botShutdown()
            
    def restartBot(self, update, context):
        if not self.checkCommandIsOld(update.message):
            context.bot.send_message(chat_id=update.message.chat_id,
                                     text='Restarting this bot.')
            print("Restarting the bot.")
            self.botRestart()
            
        
    def runScriptAndSendFile(self, update, context):
        if not self.checkCommandIsOld(update.message):
            context.bot.send_message(chat_id=update.message.chat_id,
                             text='Please wait while we run the script..')
            
            script = context.args[0]
            file = context.args[1]
            self.runScriptToFile(script,file)
            
            context.bot.sendDocument(chat_id=update.message.chat_id, document=open(file, 'rb'))
            
            # clear the file
            os.remove(file)
    
    def downloader(self, update, context):
        origName = update.message.document.file_name
        
        path2save = os.path.join(self.fileDir, origName)
        with open(path2save, 'wb') as f:
            context.bot.get_file(update.message.document).download(out=f)
            
        print('Saved to ' + path2save)
        context.bot.send_message(chat_id=update.message.chat_id,
                             text='Downloaded file ' + origName)
    
    # Automatic git updates
    def pullUpdate(self, update, context):
        gituser = os.environ['GITUSER']
        gittoken = os.environ['GITTOKEN']
        gitrepo = os.environ['GITREPO']
        gitpullstr = 'git pull https://%s:%s@github.com/%s/%s.git' % (gituser,gittoken,gituser,gitrepo)
        os.system(gitpullstr)
        context.bot.send_message(chat_id=update.message.chat_id,
                             text='Successfully updated! Run /status again to check latest commit.')
    
    
    #%% Add Handlers Wrapper
    def addHandlers(self):
        self.dispatcher.add_handler(CommandHandler('status', self.status))
        self.dispatcher.add_handler(CommandHandler('update', self.pullUpdate))
        self.dispatcher.add_handler(CommandHandler('stop', self.stopBot))
        self.dispatcher.add_handler(CommandHandler('restart', self.restartBot))
        print("Added CommonBot handlers.")

#%%
fileDir = ntpath.split(os.path.realpath(__file__))[0]

#%%
sgtz = pytz.timezone('Singapore')

time_bot_started = dt.datetime.now()
time_bot_started = sgtz.localize(time_bot_started) # this is the correct way

#%%
def getLocalizedTimeNow():
    return sgtz.localize(dt.datetime.now())

def checkCommandIsOld(message):
    print('Datetime message was received was '+str(message.date))
    print('Bot started at ' + str(time_bot_started))
    print('%20s : %s' % ('Message time', str(message.date.timestamp())))
    print('%20s : %s' % ('Bot start time', str(time_bot_started.timestamp())))

    if message.date.timestamp() <= time_bot_started.timestamp():
        print('old msg')
        return True
    else:
        print('new msg')
        return False

#%%
def status(update, context):
    if not checkCommandIsOld(update.message):
        timeNow = getLocalizedTimeNow()
        context.bot.send_message(chat_id=update.message.chat_id,
                         text='This bot was started at '+str(time_bot_started)+' and has been alive for '+str(timeNow-time_bot_started))

#%%
def stopBot(update, context):
    if not checkCommandIsOld(update.message):
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='Ending this bot.')
        print("Ending the bot.")
        # os.kill(os.getpid(), signal.SIGINT)
        # threading.Thread(target=botShutdown).start()
        botShutdown()
        
        
def botShutdown():
    os._exit(0) # hardcore? but always works 
    # updater.stop()
    # updater.is_idle = False

#%%
def restartBot(command, timeout=10):
    command = "start python botRestart.py seopibot_main.py"
    print(command)
    os.system(command) # we start the restart protocol
    botShutdown() # then shutdown
    
#%%
def runScriptToFile(script, file):
    with open(file,"w+") as fid:
        subprocess.call(["python", script], stdout=fid)
    
def runScriptAndSendFile(update, context):
    if not checkCommandIsOld(update.message):
        context.bot.send_message(chat_id=update.message.chat_id,
                         text='Please wait while we run the script..')
        
        script = context.args[0]
        file = context.args[1]
        runScriptToFile(script,file)
        
        context.bot.sendDocument(chat_id=update.message.chat_id, document=open(file, 'rb'))
        
        # clear the file
        os.remove(file)

#%% file management
def zipFiles(filepaths, zipfilepath, cl=9):
    '''Compression levels 0 (no compression) to 9 (max compression)'''
    z = zipfile.ZipFile(zipfilepath,'w', compression=zipfile.ZIP_DEFLATED, compresslevel=cl)
    
    for fp in filepaths:
        z.write(fp)
    
    z.close()
    
    
#%%
def downloader(update, context):
    origName = update.message.document.file_name
    
    path2save = os.path.join(ntpath.split(os.path.realpath(__file__))[0], origName)
    with open(path2save, 'wb') as f:
        context.bot.get_file(update.message.document).download(out=f)
        
    print('Saved to ' + path2save)
    context.bot.send_message(chat_id=update.message.chat_id,
                         text='Downloaded file ' + origName)

#%% Automatic git updates
def pullUpdate(update, context):
    os.system('git pull')

#%%
if __name__=="__main__":
    
    class SpecialBot(CommonBot):
        def __init__(self):
            super().__init__() # you must include this line
            
            # do some things
            
            # do not do this again
            # self.addHandlers()
            
            print("Special bot initializer.")
            
        # either overload this method and use super like this,
        # or make an extra method to add the new handlers
        def addHandlers(self):
            super().addHandlers() # you must include this line
            print("Added Special bot handlers.")
            
    sb = SpecialBot()