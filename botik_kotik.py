import os
import flask
import telebot  # импортируем модуль pyTelegramBotAPI
import conf
from telebot import types

WEBHOOK_URL_BASE = "https://{}:{}".format(conf.WEBHOOK_HOST, conf.WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(conf.TOKEN)

bot = telebot.TeleBot(conf.TOKEN,threaded=False)

# удаляем предыдущие вебхуки, если они были
bot.remove_webhook()

# ставим новый вебхук = Слышь, если кто мне напишет, стукни сюда — url
bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH)

app = flask.Flask(__name__)
## Часть 1: обращаемся к папке "Песни" и записываем нужную инфу в переменные

tree = os.walk('/home/PollyTulip/With_love/Песни')

songs_with_gaps = {} # название песни : название файлов с текстами песен с пропусками
songs_with_mp3 = {}  # название песни : название файла с музыкой

for i in tree:
    songs_names = i[1]
    break
for song in songs_names:
    songs_with_gaps [song] = []
    songs_with_mp3 [song] = ''

for song in songs_with_gaps:
    folder_the_song = os.walk(f'/home/PollyTulip/With_love/Песни/{song}') #папка с конкретной песней
    for inner in folder_the_song:
        for inny in inner:
            if  type (inny) == list and len(inny)!=0: #добираемся до листа с текстами песни и аудио
                for file in inny:
                    if f'{song}_' in file:
                        songs_with_gaps[song].append (file) #добавляем названия текстов с пропусками


for song in  songs_with_mp3:
    folder_the_song = os.walk(f'/home/PollyTulip/With_love/Песни/{song}') #папка с конкретной песней
    for inner in folder_the_song:
        for inny in inner:
            if  type (inny) == list and len(inny)!=0: #добираемся до листа с текстами песни и аудио
                for file in inny:
                    if f'.mp3' in file:
                        songs_with_mp3 [song] = file #добавляем название аудио

## Часть 2: бот

# команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, '''Слушай песни на русском, вставляй слова и проверяй себя!

/full_text -- список песен и их полный текст

/text_with_gaps -- список песен и их текст с пропусками.

Могут быть пропущены разные слова, например:
A	прилагательные
S	существительные
V	глаголы

Послушай песни, вставь слова в пропуски, а потом открой полный текст и проверь себя. Удачи!
''')

# команда /full_text

@bot.message_handler(commands=["full_text"])
def send_songs_texts(message):

    keyboard = types.InlineKeyboardMarkup()

    global songs_list
    songs_list = {}
    number = 0
    for song_name in songs_names:
        number+=1
        button = types.InlineKeyboardButton(text=song_name, callback_data=f'f_song{number}')
        songs_list[number] = song_name
        keyboard.add(button)

    bot.send_message(message.chat.id, "У меня есть такие песни:", reply_markup=keyboard)


# команда /text_with_gaps

@bot.message_handler(commands=["text_with_gaps"])
def send_gapped_text(message):

    keyboard = types.InlineKeyboardMarkup()

    global songs_list
    songs_list = {}
    number = 0
    for song_name in songs_names:
        number+=1
        button = types.InlineKeyboardButton(text=song_name, callback_data=f'song{number}')
        songs_list[number] = song_name
        keyboard.add(button)

    bot.send_message(message.chat.id, "Выбери песню:", reply_markup=keyboard)


# колбэки
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        for i in songs_list:
            if call.data == f'f_song{i}':
                with open (f"/home/PollyTulip/With_love/Песни/{songs_list[i]}/{songs_list[i]}.txt", 'r') as f:
                    song_text = ''
                    for line in f:
                        song_text += line
                bot.send_message (call.message.chat.id, song_text)

        for i in songs_list:
            if call.data == f'song{i}':
                gapped_songs = types.InlineKeyboardMarkup()
                number = 0
                global g_song_list
                g_song_list = {}
                for g_song in songs_with_gaps[songs_list[i]]:
                    number+=1
                    g_song_list[number] = [songs_list[i],g_song]
                    button_2 = types.InlineKeyboardButton(text=g_song, callback_data=f'g_song{number}')
                    gapped_songs.add(button_2)
                bot.edit_message_text('С какими пропусками?', call.message.chat.id, call.message.message_id,
                              reply_markup=gapped_songs)

        for i in g_song_list:
            if call.data == f'g_song{i}':
                with open (f"/home/PollyTulip/With_love/Песни/{g_song_list[i][0]}/{g_song_list[i][1]}", 'r') as f:
                    g_song_text = ''
                    for line in f:
                        g_song_text += line
                bot.send_message (call.message.chat.id, g_song_text)

                with open (f"/home/PollyTulip/With_love/Песни/{g_song_list[i][0]}/{songs_with_mp3[g_song_list[i][0]]}", 'rb') as audio:
                    bot.send_audio (call.message.chat.id, audio)

# запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)

# пустая главная страничка для проверки
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'ok'


# обрабатываем вызовы вебхука = функция, которая запускается, когда к нам постучался телеграм
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


