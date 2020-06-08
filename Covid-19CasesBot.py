#!/usr/bin/env python
# -*- coding: utf-8 -*-

import config
import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import casesdata

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# States of conversation to add Landkreis
ASKFORLK, CHOOSELK, REMOVELK = range(3)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    user = update.message.from_user
    update.message.reply_text(
        'Hallo ' + user.first_name + '!\n'
        'Gib einen gewünschten Lankreis ein.')
    return ASKFORLK

def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

def newlk(update, context):
    update.message.reply_text('Gib einen gewünschten Landkreis ein.')
    return ASKFORLK

def removelk(update, context):
    reply_keyboard = []
    userlks = casesdata.lks_of_user(update.message.chat_id)
    if len(userlks) > 0:
        for lk in userlks:
            reply_keyboard.append([lk])
        update.message.reply_text(
            'Welchen Landkreis möchtest du löschen?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return REMOVELK
    else:
        return ConversationHandler.END


# Helper methods.
def ask_for_landkreis(update, context):
    results = casesdata.get_rki_landkreise(update.message.text, exact=False)
    if len(results) == 1:
        lk = results[0]['attributes']['GEN']
        casesdata.add_entry(lk, update.message.chat_id)
        update.message.reply_text('Alles klar, du erhältst jetzt Updates für den Landkreis ' + lk + '.')
        return ConversationHandler.END
    else:
        reply_keyboard = []
        for res in results:
            lk = res['attributes']['GEN']
            reply_keyboard.append([lk])
        
        update.message.reply_text(
            'Ich habe mehrere Landkreise gefunden. Wähle einen aus.',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return CHOOSELK

def choose_landkreis(update, context):
    results = casesdata.get_rki_landkreise(update.message.text, exact=True)
    lk = results[0]['attributes']['GEN']
    casesdata.add_entry(lk, update.message.chat_id)
    update.message.reply_text('Alles klar, du erhältst jetzt Updates für den Landkreis ' + lk + '.')
    return ConversationHandler.END

def remove_landkreis(update, context):
    casesdata.remove_entry(update.message.text, update.message.chat_id)
    update.message.reply_text('Erledigt, du erhältst für den Landkreis ' + update.message.text + ' keine Infos mehr.')
    return ConversationHandler.END

def status(update, context):
    userlks = casesdata.lks_of_user(update.message.chat_id)
    if len(userlks) > 0:
        for lk in userlks:
            update.message.reply_text(casesdata.info_for_landkreis(lk), parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(
            'Du hast noch keinen gewünschten Landkreis angegeben.\n'
            'Verwende dafür den Befehl /newlk')

def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Okay, dann ein anderes Mal.')
    
    return ConversationHandler.END

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():

    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(config.bottoken, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    # dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("status", status))

    # Add conversation handler with the states ASKFORLK, UNIQUELK, MULTIPLELK
    conv_handler = ConversationHandler(
        entry_points = [
            CommandHandler('start', start), 
            CommandHandler('newlk', newlk),
            CommandHandler('removelk', removelk)
        ],
        states = {
            ASKFORLK: [MessageHandler(Filters.text, ask_for_landkreis)],
            CHOOSELK: [MessageHandler(Filters.text, choose_landkreis)],
            REMOVELK: [MessageHandler(Filters.text, remove_landkreis)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)

    # Error handler
    dp.add_error_handler(error)

    # Read the existing data
    casesdata.load_data()
    
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()