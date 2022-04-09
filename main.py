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


class ClickerBot:
    def __init__(self, vk_session, db_sess):
        self.vk_session = vk_session
        self.db_session = db_sess
        self.waiting_for_authorization = False  # Если True, то ждет сообщения с ником для регистрации
        self.keyboard = self.create_keyboard()
        self.modificators_keyboard = None
        self.texts = ['клик 👆🏻', 'модификаторы 💲', 'баланс 💰']

    def accept_message(self, obj):
        if self.waiting_for_authorization:
            auth = check_valid_nickname(obj.message['text'])
            if auth[0]:
                add_user(obj.message['from_id'], obj.message['text'], self.db_session)
                self.reply_to_user('Отлично! Напиши "старт" чтобы начать!', obj)
                self.waiting_for_authorization = False
            else:
                self.reply_to_user(auth[1], obj)
        else:
            if not check_user(obj.message['from_id'], self.db_session):
                self.reply_to_user('Привет! Вижу, ты впервые у нас', obj)
                self.reply_to_user(
                    'Напиши свой ник, и я тебя запомню\n'
                    'Внимание! Имя не должно начинаться или заканчиваться на цифры или недопустимые символы!\n'
                    'Для помощи пиши "помощь"',
                    obj)
                self.waiting_for_authorization = True
            else:
                text = obj.message['text'].lower()
                if text == 'помощь' and check_user(obj.message['from_id'], self.db_session):
                    self.reply_to_user('кнопка клик: получить коины\n'
                                       'модификаторы: информация о модификаторах\n'
                                       'баланс: информация о вашем балансе\n'
                                       'Для начала пиши "старт"!\n'
                                       'Если бот не работает - напиши "старт" и все заработает!', obj)
                elif text != 'помощь' and text != 'старт' and text != self.texts[0] and text != self.texts[1] and text != self.texts[2]:
                    self.reply_to_user('Пиши "помощь"', obj)
                elif text == 'старт':
                    self.reply_to_user('Удачи!', obj, self.keyboard)
                elif self.texts[0] == text:
                    rand = random.randint(1, 5)
                    self.reply_to_user(f'+ {rand} коинов', obj, self.keyboard)
                    add_coins(obj.message['from_id'], rand, self.db_session)
                elif self.texts[1] == text:
                    self.reply_to_user('В разработке!', obj, self.modificators_keyboard)
                elif self.texts[2] == text:
                    coins = get_balance(obj.message["from_id"], self.db_session)
                    self.reply_to_user(f'У вас {coins} монет', obj, self.keyboard)

    def reply_to_user(self, text, obj, kboard=None):
        vk = vk_session.get_api()
        vk.messages.send(user_id=obj.message['from_id'],
                         message=text,
                         random_id=random.randint(0, 2 ** 64),
                         keyboard=kboard)

    def create_keyboard(self):
        keyboard = vk_api.keyboard.VkKeyboard(one_time=False)
        keyboard.add_button("Клик 👆🏻", color=vk_api.keyboard.VkKeyboardColor.SECONDARY)
        keyboard.add_button("Модификаторы 💲", color=vk_api.keyboard.VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button("Баланс 💰", color=vk_api.keyboard.VkKeyboardColor.POSITIVE)
        return keyboard.get_keyboard()


def add_user(uid, nickname, sess):
    global User
    u = User()
    u.uid = str(uid)
    u.nickname = nickname
    sess.add(u)
    sess.commit()


def add_coins(uid, coins, sess):
    global User
    save = sess.query(User).filter_by(uid=uid).first()
    save.clicks += coins
    sess.commit()


def get_balance(uid, sess):
    global User
    return (sess.query(User).filter_by(uid=uid).first()).clicks


def check_user(uid, db_sess):  # проверяет наличие пользователя в базе
    global User
    users = db_sess.query(User).all()
    for user in users:
        if user.uid == str(uid):
            return True
    return False


def check_valid_nickname(nickname: str):
    valid = True
    reason = None
    for symbol in '''!'1234567890@#$%^&*()_+{}:"?><][';/.,'"-=`~/*\|''':
        if nickname.startswith(symbol):
            return [False, 'Ошибка: Имя начинается с недопустимого символа!']
        elif nickname.endswith(symbol):
            return [False, 'Ошибка: Имя заканчивается на недопустимый символ!']
    for symb in '''!'^()+{}:"?';/.,'"-=`~/*\|''':
        if symb in nickname:
            return [False, 'Ошибка: Внутри имени недопустимый символ!']
    return [True, '']

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



def main(vk_session, session, bot, datetime):
    longpoll = VkBotLongPoll(vk_session, group_id='212227596')

    for event in longpoll.listen():
        check_time_to_commit(session, datetime)

        if event.type == VkBotEventType.MESSAGE_NEW:
            vk = vk_session.get_api()
            bot.accept_message(event.obj)
            print('Сообщение', event.obj.message['text'])


if __name__ == '__main__':
    db_session.global_init('data/db/clicker_db.sqlite')
    session = db_session.create_session()
    vk_session = vk_api.VkApi(token=TOKEN)
    bot = ClickerBot(vk_session, session)
    main(vk_session, session, bot, datetime)
