import json
import logging
import os
from datetime import date, datetime

from dateutil import relativedelta
from pid.decorator import pidfile
from PIL import Image, ImageDraw, ImageFont
from telegram import (Bot, ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from config import start_msg, token
import matplotlib.pyplot as plt

bot = Bot(token)


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

plt.set_loglevel('WARNING')
# Conversation states
SEND_RESULT = range(1)


def makeUser(id_user, date, km, readData):
    # add user and timestamp
    data = {'id_user': id_user,
            'list_km': [{'date': date, 'km': int(km)}]}
    readData.append(data)

    # save file
    with open(os.getcwd() + '/data.json', 'w') as file:
        json.dump(readData, file, indent=3)


def get_text_dimensions(text_string, font):
    text_width = font.getmask(text_string).getbbox()[2]
    return int(text_width)


def make_bg(id_user, text1, text2, text3, text4):
    background = 'template.png'
    font = ImageFont.truetype(str('font/font-regular.ttf'), 68)
    font1 = ImageFont.truetype(str('font/font-bold.ttf'), 68)
    font2 = ImageFont.truetype(str('font/font-bold.ttf'), 50)
    font3 = ImageFont.truetype(str('font/font-bold.ttf'), 100)

    backgroundsave = f'{id_user}.png'
    #
    background_image = Image.open(background, "r")
    draw = ImageDraw.Draw(background_image)

    draw.text((340, 130), 'Riepilogo', (255, 255, 255), font=font3)
    draw.text((65, 900), 'Totali', (16, 124, 206), font=font)
    draw.text((625, 900), 'Mensili', (16, 124, 206), font=font)
    draw.text((65, 1290), 'Media', (16, 124, 206), font=font)
    draw.text((625, 1290), 'Tracciati', (16, 124, 206), font=font)

    draw.text((75, 1050), text1, (255, 255, 255), font=font1)
    draw.text((75+get_text_dimensions(text1, font1), 1050+18),
              ' KM', (255, 255, 255), font=font2)
    #
    draw.text((635, 1050), text2, (255, 255, 255), font=font1)
    draw.text((635+get_text_dimensions(text2, font1), 1050+18),
              ' KM', (255, 255, 255), font=font2)
    #
    draw.text((75, 1440), text3, (255, 255, 255), font=font1)
    draw.text((75+get_text_dimensions(text3, font1), 1440+18),
              ' KM', (255, 255, 255), font=font2)
    #
    draw.text((635, 1440), text4, (255, 255, 255), font=font1)
    draw.text((635+get_text_dimensions(text4, font1), 1440+18),
              ' KM', (255, 255, 255), font=font2)

    im2 = Image.open('graph.png')
    background_image.paste(im2, (200, 250), im2.convert('RGBA'))
    background_image.save(f"{os.getcwd()}/data_info/{backgroundsave}")


def make_graph(array, array2):
    plt.rcParams['axes.facecolor'] = '#262626'
    plt.rcParams['axes.axisbelow'] = True
    plt.style.use('dark_background')
    fig, ax = plt.subplots(nrows=1, ncols=1)  # create figure & 1 axis

    array3 = []

    for i in range(len(array)):
        array3.append(
            f'{array[i].split("-")[1]}/{array[i].split("-")[0].replace("20","")} ')

    ax.bar(array3, array2, color='#107cce', edgecolor='#195786')
    ax.set_ylim(array2[0]-1000, array2[-1]+1000)
    plt.grid(True, axis='y')
    ax.spines.right.set_visible(False)
    ax.spines.top.set_visible(False)
    ax.spines.bottom.set_visible(False)
    ax.spines.left.set_visible(False)

    # save the figure to file+
    fig.savefig('graph.png', transparent=True,  dpi=120)
    plt.close(fig)


def getKM(id_user, readData):
    message = ''
    array = []
    array2 = []
    for i in range(len(readData)):
        if readData[i]['id_user'] == id_user:

            arraylen = len(readData[i]['list_km'])
            for k in range(arraylen):
                array.append(str(readData[i]['list_km'][k]['date']))
                array2.append(readData[i]['list_km'][k]['km'])

            make_graph(array, array2)

            text1 = str(format(readData[i]['list_km']
                        [-1]['km'], ',d')).replace(',', '.')

            message += f"KM totali: `{text1}`\n"

            lastdatakm = readData[i]['list_km'][-1]['km']
            firstdatakm = readData[i]['list_km'][0]['km']

            try:
                text2 = str(format(int(lastdatakm - round(
                    readData[i]['list_km'][-2]['km'])), ',d')).replace(',', '.')
                message += f"KM rispetto allo scorso mese: `{str(format(int(lastdatakm - round(readData[i]['list_km'][-2]['km'])),',d')).replace(',','.')}`\n"
            except:
                text2 = "0"
                pass
            text3 = str(format(int((lastdatakm - readData[i]
                        ['list_km'][0]['km']) / arraylen), ',d')).replace(',', '.')
            text4 = str(format(int(
                (lastdatakm - firstdatakm)), ',d')).replace(',', '.')
            message += f"KM in media al mese: `{str(format(int((lastdatakm - firstdatakm) / arraylen), ',d')).replace(',','.')}`\n"
            message += f"KM percorsi dal monitoraggio: `{str(format(int((lastdatakm - firstdatakm)), ',d')).replace(',','.')}`\n"

            make_bg(id_user, text1, text2, text3, text4)

    return message


def addKilometers(id_user, date, km, readData):
    # add Kilometers

    list_km = []
    for i in range(len(readData)):
        id_user_json = readData[i]['id_user']
        if id_user_json == id_user:
            list_km = (readData[i]['list_km'])

    now = datetime.now()
    start = datetime.strptime(list_km[-1]['date'], "%Y-%m-%d")
    end = datetime.strptime(now.strftime("%Y-%m-%d"), "%Y-%m-%d")

    res = (end.year - start.year) * 12 + (end.month - start.month)
    if res != 0:

        for i in range(len(readData)):
            id_user_json = readData[i]['id_user']
            if id_user_json == id_user:
                list_km = readData[i]['list_km']
                data = {'date': date, 'km': int(km)}
                list_km.append(data)

                # save file
                with open(os.getcwd() + '/data.json', 'w') as file:
                    json.dump(readData, file, indent=3)
    else:

        for i in range(len(readData)):
            id_user_json = readData[i]['id_user']
            if id_user_json == id_user:
                for j in range(len(readData[i]['list_km'])):

                    new_date = str(readData[i]['list_km']
                                   [j]['date']).split('-')
                    new_date = f"{new_date[0]}-{new_date[1]}"

                    if now.strftime("%Y-%m") == new_date:

                        list_km_delete = readData[i]['list_km']
                        list_km_delete.pop(j)

                        # save file
                        with open(os.getcwd() + '/data.json', 'w') as file:
                            json.dump(readData, file,  indent=3)

        for i in range(len(readData)):
            id_user_json = readData[i]['id_user']
            if id_user_json == id_user:
                list_km = readData[i]['list_km']
                data = {'date': date, 'km': int(km)}
                list_km.append(data)

                # save file
                with open(os.getcwd() + '/data.json', 'w') as file:
                    json.dump(readData, file,  indent=3)


def checkDiff(date, new_error, readData):

    id_user = []
    for i in range(len(readData)):
        for j in range(len(readData[i]['list_km'])):
            if date == readData[i]['list_km'][j]['date']:
                error_json = int(readData[i]['list_km'][j]['km'])
                if error_json != new_error:
                    id_user.append(readData[i]['id_user'])
                    readData[i]['list_km'][j]['km'] = new_error

                    # save file
                    with open(os.getcwd() + '/data.json', 'w') as file:
                        json.dump(readData, file,  indent=3)

    return id_user


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(start_msg, parse_mode='Markdown')


def start_search(update: Update, context: CallbackContext) -> int:
    context.user_data['last_search'] = {}

    update.message.reply_text(
        '*Inserisci KM della tua auto*',
        parse_mode='Markdown'
    )
    return SEND_RESULT


def send_result(update: Update, context: CallbackContext) -> int:
    response = update['message']['text'].replace('.', '')
    context.user_data['last_search']['username'] = response

    reply_markup = ''
    if "/" in response:
        update.message.reply_text(
            '*Qualcosa è andato storto 😕*',
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    context.user_data['last_message'] = bot.send_message(chat_id=update['message']['chat']['id'], text="*Aggiungo...*",
                                                         reply_markup=ReplyKeyboardRemove(),
                                                         parse_mode='Markdown'
                                                         )

    with open(os.getcwd() + "/data.json", "r") as f:
        readData = json.load(f)

    for k in range(len(readData)):

        resultKM = getKM(update['message']
                         ['chat']['id'], readData)

        if resultKM == '':
            makeUser(update['message']['chat']
                     ['id'], str(date.today()), response, readData)

            print(str(date.today()))
            last_message = context.user_data['last_message']
            bot.delete_message(
                chat_id=update.effective_chat.id, message_id=last_message.message_id)

            result = getKM(update['message']
                           ['chat']['id'], readData)
            context.user_data['last_message'] = result
            bot.send_photo(
                chat_id=update['message']['chat']['id'],
                photo=open(
                    f"{os.getcwd()}/data_info/{update['message']['chat']['id']}.png", 'rb'),

                caption=result,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

            return ConversationHandler.END

        else:
            if readData[k]['id_user'] == update['message']['chat']['id']:
                if len(readData[k]['list_km']) != 0:

                    try:
                        if readData[k]['list_km'][-1]['km'] < int(response):

                            addKilometers(update['message']['chat']
                                          ['id'], str(date.today()), response, readData)

                            print(str(date.today()))
                            last_message = context.user_data['last_message']
                            bot.delete_message(
                                chat_id=update.effective_chat.id, message_id=last_message.message_id)

                            result = getKM(update['message']
                                           ['chat']['id'], readData)
                            context.user_data['last_message'] = result
                            bot.send_photo(
                                chat_id=update['message']['chat']['id'],
                                photo=open(
                                    f"{os.getcwd()}/data_info/{update['message']['chat']['id']}.png", 'rb'),
                                caption=result,
                                reply_markup=reply_markup,
                                parse_mode='Markdown'
                            )
                            return ConversationHandler.END

                        else:
                            last_message = context.user_data['last_message']
                            bot.delete_message(
                                chat_id=update.effective_chat.id, message_id=last_message.message_id)
                            context.user_data['last_message'] = bot.send_message(chat_id=update['message']['chat']['id'], text='*KM minori rispetto ai precedenti, riprova...*',
                                                                                 parse_mode='Markdown'
                                                                                 )
                    except:
                        last_message = context.user_data['last_message']
                        bot.delete_message(
                            chat_id=update.effective_chat.id, message_id=last_message.message_id)
                        context.user_data['last_message'] = bot.send_message(chat_id=update['message']['chat']['id'], text='*Inserisci un numero non una stringa, riprova...*',
                                                                             parse_mode='Markdown'
                                                                             )


def send_credits(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        '*Bot developed by*:\n'
        '• [Fast0n](https://github.com/fast0n)\n',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    return None


def info_car(update: Update, context: CallbackContext) -> int:

    with open(os.getcwd() + "/data.json", "r") as f:
        readData = json.load(f)

    result = getKM(update['message']
                   ['chat']['id'], readData)

    try:
        if result == '':
            bot.send_message(
                chat_id=update['message']['chat']['id'],

                text="Nessun risultato trovato...\nProva con /aggiungi",
                parse_mode='Markdown'
            )
        else:
            bot.send_photo(
                chat_id=update['message']['chat']['id'],
                photo=open(
                    f"{os.getcwd()}/data_info/{update['message']['chat']['id']}.png", 'rb'),

                caption=result,
                parse_mode='Markdown'
            )
    except:
        bot.send_message(
            chat_id=update['message']['chat']['id'],

            text="Nessun risultato trovato...\nProva con /aggiungi",
            parse_mode='Markdown'
        )
    return ConversationHandler.END


def conversation_fallback(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        '*Qualcosa è andato storto 😕*',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    return ConversationHandler.END


@ pidfile('/tmp/kmautotracker.pid')
def main():
    print("--- Starting kmautotracker ---")

    if not os.path.exists(os.getcwd() + '/data.json'):
        f = open(os.getcwd() + '/data.json', 'w+')
        f.write('[]')
        f.close()

    # Setup bot
    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher

    # Add command handlers
    start_handler = CommandHandler('start', start)
    credits_handler = CommandHandler('crediti', send_credits)
    list_saved_players_handler = CommandHandler('info', info_car)

    search_handler = ConversationHandler(
        entry_points=[CommandHandler('aggiungi', start_search)],
        states={
            SEND_RESULT: [
                MessageHandler(Filters.text, send_result),
            ]
        },
        fallbacks=[MessageHandler(Filters.update, conversation_fallback)],
    )

    dispatcher.add_handler(list_saved_players_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(search_handler)
    dispatcher.add_handler(credits_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
