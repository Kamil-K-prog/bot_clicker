import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random
import datetime
from data import db_session
from data.user import User
from data.modificators import Modificators

TOKEN = 'cccf1a05dec0e26b5388dbaf2190362a2a4c2692f7aeebe98b36b2c19031ad1980136723e8bbea17879ed'
BOT_START_TIME = datetime.datetime.now()
saved_time = datetime.datetime.now()


def write_log(text):
    with open('data/logs/logs.txt', 'a') as logfile:
        logfile.write(f'[{datetime.datetime.now()}] : {text}\n')


class ClickerBot:
    def __init__(self, vk_session, db_sess):
        self.vk_session = vk_session
        self.db_session = db_sess
        self.waiting_for_authorization = False  # Если True, то ждет сообщения с ником для регистрации
        self.keyboard = self.create_keyboard()
        self.modificators_keyboard = self.create_modificator_keyboard()
        self.agreement_keyboard = self.create_agreement_keyboard()
        self.functions_keyboard = self.create_functions_keyboard()
        self.helping_keyboard = self.create_helping_leyboard()
        self.back_keyboard = self.create_back_keyboard()
        self.in_modificators = False
        mods = [i[0] for i in get_modificators(self.db_session)]
        self.ids = [i[1] for i in get_modificators(self.db_session)]
        self.texts = ['клик 👆🏻', 'модификаторы 💲', 'баланс 💰', '🔙 back', 'функции ⚙', 'передача валюты',
                      'получить анекдот', *mods]
        self.price = None
        self.want_to_buy = False
        self.m_id = 0
        self.in_functions = False
        self.in_exchange = False
        self.accept_exchange = False
        self.in_value_changing = False
        self.nickname_to_exchange = ''
        self.anekdots = all_anekdots()
        self.rofls = []
        self.value_to_exchange = 0
        self.nicknames_list = get_nicknames_list(self.db_session)
        print(self.nicknames_list)

    def accept_message(self, obj):
        uid = obj.message['from_id']
        text_mes = obj.message['text']
        text = text_mes.lower()

        if text_mes.lower() not in self.texts and '⚙' not in text_mes:
            write_log(f'Resieved message from uid = "{uid}" and text = "{text_mes}"')

        else:
            if text == self.texts[0]:
                write_log(f'User with uid = "{uid}" clicked')
            if text == self.texts[1]:
                write_log(f'User with uid = "{uid}" got modificators list')
            if text == self.texts[2]:
                write_log(f'User with uid = "{uid}" got balance')
            if text == self.texts[4]:
                write_log(f'User with uid = "{uid}" got functions list')
            if text == self.texts[5]:
                write_log(f'User with uid = "{uid}" decided to transfer the coins')

        if self.waiting_for_authorization:
            auth = check_valid_nickname(text_mes, self.db_session, self.texts)
            if auth[0]:
                add_user(uid, text_mes, self.db_session)
                self.nicknames_list += text_mes
                self.reply_to_user('Отлично! Напиши "старт" чтобы начать!', obj)
                self.waiting_for_authorization = False
            else:
                self.reply_to_user(auth[1], obj)
        else:
            if not check_user(uid, self.db_session):
                self.reply_to_user('Привет! Вижу, ты впервые у нас', obj)
                self.reply_to_user(
                    'Напиши свой ник, и я тебя запомню\n'
                    'Внимание! Имя не должно начинаться или заканчиваться на цифры или недопустимые символы!\n',
                    obj)
                self.waiting_for_authorization = True
            else:
                if text == 'помощь' and check_user(uid, self.db_session):
                    self.reply_to_user('Кнопка клик: получить коины\n'
                                       'Модификаторы: информация о модификаторах\n'
                                       'Баланс: информация о вашем балансе\n'
                                       'Для начала пиши/нажимай "старт"\n'
                                       'Если бот не работает - напиши/нажми "рестарт" и все заработает!', obj,
                                       self.helping_keyboard)
                if text != 'помощь' and text != 'старт' and text != 'рестарт' and text not in self.texts and text not \
                        in ['да', 'нет'] and text_mes not in self.nicknames_list:
                    print(self.texts)
                    self.reply_to_user('Пиши или нажимай "Помощь"\nЕсли бот завис - напиши или нажми "Старт"', obj,
                                       self.helping_keyboard)
                if text == 'старт' or text == 'рестарт':
                    self.reply_to_user('Удачи!', obj, self.keyboard)
                    self.in_modificators, \
                    self.in_exchange, \
                    self.in_functions = False, False, False
                    print(self.texts)

                elif self.texts[0] == text and not self.in_modificators:
                    user_modificator = get_user_modificator(obj.message['from_id'], self.db_session)
                    rand = random.randint(1, 10) * user_modificator
                    self.reply_to_user(f'+ {rand} коинов', obj, self.keyboard)
                    add_coins(obj.message['from_id'], rand, self.db_session)
                    write_log(f'User with uid = "{uid}" recieved {rand} coins')

                elif self.texts[1] == text and not self.in_modificators:
                    self.reply_to_user('Нажатие на модификатор вернет информацию о нем', obj,
                                       self.modificators_keyboard)
                    self.in_modificators = True

                elif self.texts[2] == text and not self.in_modificators:
                    coins = get_balance(obj.message["from_id"], self.db_session)
                    self.reply_to_user(f'У вас {coins} монет', obj, self.keyboard)

                elif text == self.texts[3] and self.in_modificators:
                    self.in_modificators = False
                    self.reply_to_user('Возвращаемся...', obj, self.keyboard)

                elif text in self.texts[7:] and self.in_modificators:
                    self.m_id = self.texts.index(text) - 6
                    price, multiplier = get_price_and_multiplier_of_modificator(self.m_id, self.db_session)
                    self.reply_to_user(f'Увеличивает в {multiplier} раза количество получаемых коинов.\n'
                                       f'Стоимость: {price}', obj, self.modificators_keyboard)

                    self.want_to_buy = True
                if self.want_to_buy and text not in ['старт', 'да', 'нет']:
                    self.reply_to_user('Хочешь приобрести?', obj, self.agreement_keyboard)

                elif self.want_to_buy and text == 'да' or text == 'нет':
                    self.want_to_buy = False
                    op = check_can_be_bought(obj.message['from_id'], self.m_id, self.db_session)
                    if op and text == 'да':
                        self.reply_to_user('Поздравляем с успешной покупкой!', obj, self.modificators_keyboard)
                        set_modificator(obj.message['from_id'], self.m_id, self.db_session)
                    elif op is False and text == 'да':
                        self.reply_to_user('На вашем балансе недостаточно средств или у вас уже куплен '
                                           'модификатор равный или лучше этого.', obj, self.modificators_keyboard)
                    elif text == 'нет':
                        self.reply_to_user('Продолжаем...', obj, self.modificators_keyboard)
                    obj.message['text'] = 'старт'


                elif text_mes == 'Функции ⚙' and not (self.in_modificators or self.in_functions or self.in_exchange):
                    self.in_functions = True
                    print(self.in_functions)
                    self.reply_to_user('Открыто меню функций', obj, self.functions_keyboard)

                elif self.in_value_changing:
                    if text == self.texts[3]:
                        self.in_exchange, self.in_value_changing = False, False
                    try:
                        if check_value_to_exchange(uid, int(text_mes),
                                                   self.db_session) and not \
                                get_user_nickname_on_uid(uid, self.nickname_to_exchange, self.db_session):
                            self.value_to_exchange = int(text_mes)
                            write_log(
                                f'User with uid = "{uid}" gave to the user with nickname = "{text_mes}" '
                                f'{self.value_to_exchange} coins')
                            self.reply_to_user('Успешно передано', obj, self.functions_keyboard)
                            do_exchange(self.value_to_exchange, uid, self.nickname_to_exchange, self.db_session)
                            self.in_exchange, self.in_value_changing, self.nickname_to_exchange, \
                            self.value_to_exchange = False, False, '', 0
                        elif get_user_nickname_on_uid(uid, self.nickname_to_exchange, self.db_session):
                            self.reply_to_user("Ты серьезно решил передать коины себе? Не надо так", obj,
                                               self.back_keyboard)
                        else:
                            self.reply_to_user('Введена неправильная сумма!', obj, self.back_keyboard)
                    except ValueError:
                        self.reply_to_user('В твоем сообщении присутсвуют символы, отличные от цифр. Попробуй еще раз',
                                           obj, self.back_keyboard)

                elif self.in_functions and not self.in_exchange and not self.in_value_changing:
                    if text == self.texts[5]:
                        self.reply_to_user('Открыто меню передачи\nНапиши ник игрока, которому хочешь передать коины',
                                           obj, self.back_keyboard)
                        self.in_exchange = True

                    if text == self.texts[6]:
                        self.reply_to_user(self.get_rofl(), obj, self.functions_keyboard)
                    if text == self.texts[3]:
                        self.reply_to_user('Возвращаемся...', obj, self.keyboard)
                        self.in_functions = False
                        print(self.in_functions)

                elif self.in_exchange and not self.in_value_changing:
                    nn = check_user_on_nickname(text_mes, self.db_session)
                    if text == self.texts[3]:
                        self.in_exchange = False
                        self.reply_to_user('Возвращаемся...', obj, self.functions_keyboard)
                    elif nn:
                        self.nickname_to_exchange = text_mes
                        self.reply_to_user('Отлично, теперь введи сумму, которую хочешь передать', obj,
                                           self.back_keyboard)
                        self.in_value_changing = True
                    elif not nn:
                        self.reply_to_user('Кажется, такого игрока не существует. Проверь правильность написания', obj,
                                           self.back_keyboard)

    def reply_to_user(self, text, obj, kboard=None):
        vk = vk_session.get_api()
        vk.messages.send(user_id=obj.message['from_id'],
                         message=text,
                         random_id=random.randint(0, 2 ** 64),
                         keyboard=kboard)

    def get_rofl(self):
        try:
            tmp = []
            if len(self.rofls) == 0:
                for i in self.anekdots:
                    if i != ';':
                        tmp += [i]
                    else:
                        self.rofls += [tmp[:]]
                        tmp.clear()
            rnd = random.choice(self.rofls)
            self.rofls.remove(rnd)
            return '\n'.join(rnd)
        except Exception as e:
            return 'Шутки кончились ;)'

    def create_helping_leyboard(self):
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("Старт", color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button("Помощь", color=VkKeyboardColor.SECONDARY)
        return keyboard.get_keyboard()

    def create_back_keyboard(self):
        keyboard = vk_api.keyboard.VkKeyboard()
        keyboard.add_button("🔙 Back", color=VkKeyboardColor.NEGATIVE)
        keyboard.add_button('Рестарт', color=VkKeyboardColor.SECONDARY)
        return keyboard.get_keyboard()

    def create_keyboard(self):
        keyboard = vk_api.keyboard.VkKeyboard(one_time=False)
        keyboard.add_button("Клик 👆🏻", color=VkKeyboardColor.SECONDARY)
        keyboard.add_button("Модификаторы 💲", color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button("Функции ⚙", color=VkKeyboardColor.POSITIVE)
        keyboard.add_button("Баланс 💰", color=VkKeyboardColor.POSITIVE)
        keyboard.add_button("Рестарт", color=VkKeyboardColor.NEGATIVE)
        return keyboard.get_keyboard()

    def create_modificator_keyboard(self):
        k = 1
        keyboard = VkKeyboard(one_time=False)
        mods = get_modificators(self.db_session)
        for i in range(len(mods)):
            keyboard.add_button(mods[i][0], color=VkKeyboardColor.PRIMARY)
            if k % 3 == 0:
                keyboard.add_line()
            k += 1
        print(k)
        if (k - 1) % 3 != 0:
            keyboard.add_line()
        keyboard.add_button("🔙 Back", color=VkKeyboardColor.POSITIVE)
        return keyboard.get_keyboard()

    def create_agreement_keyboard(self):
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button("Да", color=VkKeyboardColor.POSITIVE)
        keyboard.add_button("Нет", color=VkKeyboardColor.NEGATIVE)
        return keyboard.get_keyboard()

    def create_functions_keyboard(self):
        keyboard = VkKeyboard()
        keyboard.add_button("Передача валюты", color=VkKeyboardColor.PRIMARY)
        keyboard.add_button("Получить анекдот", color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button("🔙 Back", color=VkKeyboardColor.NEGATIVE)
        return keyboard.get_keyboard()


def set_modificator(uid, mod_id, sess):
    global User, Modificators
    u = sess.query(User).filter_by(uid=uid).first()
    mod = sess.query(Modificators).filter_by(id=mod_id).first()
    u.modificator = mod.id
    u.clicks -= mod.price
    sess.commit()


def add_user(uid, nickname, sess):
    global User
    u = User()
    u.uid = str(uid)
    u.nickname = nickname
    sess.add(u)
    sess.commit()
    write_log(f'Added user with uid = "{uid}" and nickname = "{nickname}"')


def add_coins(uid, coins, sess):
    global User
    save = sess.query(User).filter_by(uid=uid).first()
    save.clicks += coins
    sess.commit()


def get_balance(uid, sess):
    global User
    return (sess.query(User).filter_by(uid=uid).first()).clicks


def get_modificators(sess):
    global Modificators
    mods = sess.query(Modificators).all()
    lst = []
    for mod in mods:
        if mod.id != 0:
            lst += [(mod.name, mod.id)]
    return lst


def get_user_nickname_on_uid(uid, nickname, session: db_session):
    global User
    return (session.query(User).filter_by(uid=uid).first()).nickname == nickname


def get_user_modificator(uid, sess):
    global User
    mod = sess.query(User).filter_by(uid=uid).first()
    modificator = sess.query(Modificators).filter_by(id=mod.modificator).first()
    return modificator.multiplier


def check_can_be_bought(uid, mod_id, sess):
    global User, Modificators
    mod = sess.query(Modificators).filter_by(id=mod_id).first()
    user = sess.query(User).filter_by(uid=uid).first()
    return user.clicks >= mod.price and user.modificator < mod.id


def get_price_and_multiplier_of_modificator(id, sess):
    global Modificators
    mod = sess.query(Modificators).filter_by(id=id).first()
    return mod.price, mod.multiplier


def check_user(uid, db_sess):  # проверяет наличие пользователя в базе
    global User
    users = db_sess.query(User).all()
    for user in users:
        if user.uid == str(uid):
            return True
    return False


def check_valid_nickname(nickname: str, session, texts):
    global User
    tmp = texts + ['false', 'true']
    users = session.query(User).all()
    for text in tmp:
        if nickname in text:
            return [False, 'К сожалению, это слово зарезервировано для работы бота. Придумайте другой ник']
    for user in users:
        if user.nickname == nickname:
            return [False, 'Ошибка: Пользователь с таким именем уже зарегистрирован!']
    for symbol in '''!'1234567890@#$%^&*()_+{}:"?><][';/.,'"-=`~/*\|''':
        if nickname.startswith(symbol):
            return [False, 'Ошибка: Имя начинается с недопустимого символа!']
        elif nickname.endswith(symbol):
            return [False, 'Ошибка: Имя заканчивается на недопустимый символ!']
    for symb in '''!'^()+{}:"?';/.,'"-=`~/*\|''':
        if symb in nickname:
            return [False, 'Ошибка: Внутри имени недопустимый символ!']
    return [True, '']


def check_user_on_nickname(nickname, session):  # проверяет наличие пользователя в базе по бд
    global User
    for user in session.query(User).all():
        if nickname == user.nickname:
            return True
    return False


def get_nicknames_list(session: db_session):
    global User
    res = []
    for i in session.query(User).all():
        res.append(i.nickname)
    return res


def do_exchange(summ, sender_uid, acceptor_nickname, session: db_session):
    global User
    sender_clicks = (session.query(User).filter_by(uid=sender_uid).first()).clicks
    acceptor_clicks = (session.query(User).filter_by(nickname=acceptor_nickname).first()).clicks
    print(f'{sender_clicks} / {acceptor_clicks}')
    session.query(User).filter_by(uid=sender_uid).update({'clicks': int(sender_clicks - summ)})
    session.query(User).filter_by(nickname=acceptor_nickname).update({'clicks': int(acceptor_clicks + summ)})
    print('exchanged')
    session.commit()


def check_value_to_exchange(uid, summ, session):
    global User
    sender = session.query(User).filter_by(uid=uid).first()
    if sender.clicks >= summ:
        return True
    return False


def check_time_to_commit(session, datetime):
    global saved_time, BOT_START_TIME
    step = 1
    current_time = datetime.datetime.now()
    delta = current_time - BOT_START_TIME
    seconds = delta.total_seconds()
    minutes = (seconds % 3600) // 60
    if minutes // step >= 1 and current_time.minute != saved_time.minute:
        print(1)
        session.commit()
        saved_time = current_time
        write_log('Database changes commited')


def all_anekdots():
    with open('data/jokes/anekdots.txt', 'r', encoding='utf-8') as f:
        return list(map(str.strip, f.readlines()))


def main(vk_session, session, bot, datetime):
    longpoll = VkBotLongPoll(vk_session, group_id='212227596')

    for event in longpoll.listen():
        check_time_to_commit(session, datetime)

        if event.type == VkBotEventType.MESSAGE_NEW:
            vk = vk_session.get_api()
            bot.accept_message(event.obj)
            print('Сообщение', event.obj.message['text'])


if __name__ == '__main__':
    write_log('Program started')
    db_session.global_init('data/db/clicker_db.sqlite')
    write_log('Database initialized')
    session = db_session.create_session()
    write_log('Database session created')
    vk_session = vk_api.VkApi(token=TOKEN)
    write_log(f'VK group session created with TOKEN = "{TOKEN}"')
    bot = ClickerBot(vk_session, session)
    main(vk_session, session, bot, datetime)
