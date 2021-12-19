
import sqlite3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

#создаем переменные, для того, чтобы отслеживать, на каком этапе находится пользователь, и вызывать следующий этап
STATE = None
f_n = 1
u_a = 2
w_l = 3

# функция команды старт
def start(update, context):
    # обращение к пользователю с инструкцией того, что его дальше ждёт
    first_name = update.message.chat.first_name
    update.message.reply_text(f"Хоу-хоу-хоу, {first_name}! Вот и наступило волшебное время, когда каждый человек ждет с "
                              f"нетерпением подарков. Предлагаю принять участие в игре под названием 'Тайный Санта'. "
                              f"Каждый участник игры должен будет ввести свои данные: фамилию, имя, адрес (по которому "
                              f"он ждет подарок) и, конечно, список желаний. После ввода данных, ты получишь точно такие"
                              f" же данные о другом участнике, выбранном случайным образом. Постарайся ввести правильно "
                              f"свои данные с первого раза, обязательно проверяй их перед отправкой. Иначе твой "
                              f"Санта не сможет отправить тебе подарок(")

    # вызов функции получения полного имени
    start_getting_name_info(update, context)

def start_getting_name_info(update, context):
    global STATE
    # переменная для вызова функции обработки имени
    STATE = f_n
    update.message.reply_text(
        f"Но давай все по порядку! Для начала Санта должен узнать твои полные фамилию и имя, введи их через пробел")


def received_full_name(update, context):
    global STATE

    try:
        # ввод имени и фамилии пользователя
        user_name_text = str(update.message.text)

        # проверяем не ввел ли пользователь цифру или фамилию и имя без пробела
        flag = False
        for i in range(len(user_name_text)):
            if user_name_text[i] in "0123456789":
                flag = True
        if user_name_text.count(" ") == 0 or flag == True:
            raise ValueError(" ")

        # в случае если все введено верно, запоминаем имя
        context.user_data['full_name'] = user_name_text

        update.message.reply_text(
            f"Введи адрес, на который Санта должен прислать подарок в формате: индекс, страна, регион, район (если есть), "
            f"населенный пункт, улица, номер дома, номер квартиры/офиса")

        # изменяем глобальную переменную для вызова функции обработки адреса польователя
        STATE = u_a

    except:
        update.message.reply_text("Упс, проверь, что правильно ввел фамилию и имя (через пробел и без цифр) и напиши их еще раз")

def received_adress(update, context):
    global STATE

    try:
        user_adress_text = update.message.text

        # проверяем, ввел ли пользователь достаточно символов для адреса
        if len(user_adress_text) < 10:
            raise ValueError(" ")

        # если введено больше 10 символов, запоминаем адрес и вызываем функцию для записи списка желаний
        context.user_data['user_adress'] = user_adress_text
        update.message.reply_text(f"Класс, а теперь напиши мне свой список желаний, если такой есть. В случае его отсутсвия,"
                                  f" напиши :'Рад(-а) любому подарку'")
        STATE = w_l
    except:
        update.message.reply_text("Подозрительно мало символов... Уверен, что до канца ввел свой адрес? Попробуй еще раз")

def received_wish_list(update, context):
    global STATE

    try:
        wish_list_text = update.message.text
        full_name_data = context.user_data["full_name"]
        user_adress_data = context.user_data["user_adress"]
        wish_list_data = wish_list_text

        update.message.reply_text(f'Окей, {full_name_data}, твой адрес:{user_adress_data}, твой список '
                                  f'подароков:{wish_list_data}. '
                                  f'Именно эти данные увидит твой тайный Санта!')
        STATE = None

        # добавление данных в таблицу
        # создание таблицы с необходимыми для дальнейших операций данными
        connect = sqlite3.connect('users.db')
        cursor = connect.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS santa_data(
                full_name TEXT PRIMARY KEY,
                user_data TEXT);
            """)
        connect.commit()
        user_id = []
        user_id.append(full_name_data)
        full_user_data = 'Твой подарок ждет: {}, ' \
                         'по адресу: {}, ' \
                         'можно подарить: {}'.format(full_name_data, user_adress_data, wish_list_data)
        user_id.append(full_user_data)
        cursor.execute("INSERT INTO santa_data VALUES(?, ?);", user_id)
        connect.commit()

        update.message.reply_text(f'Введи "/dataforsanta", чтобы твой тайный Санта узнал о тебе, а ты получил данные, '
                                  f'кому отправлять подарок')


    except:
        update.message.reply_text("Что-то пошло не так...")

# функция для обработки ошибок
def error(update, context):
    update.message.reply_text('Упс, что-то пошло не так...')

# функция для обработки текста
def text(update, context):
    global STATE
    if STATE == f_n:
        return received_full_name(update, context)
    if STATE == u_a:
        return received_adress(update, context)
    if STATE == w_l:
        return received_wish_list(update, context)

# функция для вывода данных, кому пользователь должен подарить подарок
def dataforsanta(update, context):
    user_dataforsanta = calculate_dataforsanta(context.user_data['full_name'])
    update.message.reply_text(f"{user_dataforsanta}")

# функция для получения данных из общей базы данных
def calculate_dataforsanta(user_name):

    #извлекаем имя и описание из таблицы
    connect = sqlite3.connect('users.db')
    cursor = connect.cursor()
    cursor.execute("SELECT full_name FROM santa_data;")
    all_names = cursor.fetchall()
    cursor.execute("SELECT user_data FROM santa_data;")
    all_user_data = cursor.fetchall()

    # создаем "красивые" списки
    names_of_all_users = []
    for row in all_names:
        names_of_all_users.append(row[0])
    data_of_all_users = []
    for row in all_user_data:
        data_of_all_users.append(row[0])

    # перемешиваем данные пользователей, чтобы каждый получил не свои данные для отправки подарка
    shaffled_adress = data_of_all_users[1:]
    shaffled_adress.append(data_of_all_users[0])

    #создаем словарь, где ключом будет имя пользователя
    dictionary = dict(zip(names_of_all_users, shaffled_adress))

    data_for_sending = dictionary[user_name]
    return data_for_sending

def main():
    # здесь вводится токен из BotFather
    TOKEN = "5089608339:AAHl4FDg0ZAnJMAgq75IjpnWo3ITdfbixB8"
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # обработка команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("dataforsanta", dataforsanta))

    # обработка текста
    dispatcher.add_handler(MessageHandler(Filters.text, text))

    # обработка ошибок
    dispatcher.add_error_handler(error)

    # запуск бота
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()