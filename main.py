import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
from data import db_session
from data.user import User
from data.modificators import Modificators

TOKEN = 'cccf1a05dec0e26b5388dbaf2190362a2a4c2692f7aeebe98b36b2c19031ad1980136723e8bbea17879ed'


class ClickerBot:
    def __init__(self, vk_session, db_sess):
        self.vk_session = vk_session
        self.db_session = db_sess
        self.waiting_for_authorization = False  # Если True, то ждет сообщения с ником для регистрации

    def accept_message(self, obj):
        if self.waiting_for_authorization:
            auth = check_valid_nickname(obj.message['text'])
            if auth[0]:
                add_user(obj.message['from_id'], obj.message['text'], self.db_session)
                self.reply_to_user('Отлично!', obj)
                self.waiting_for_authorization = False
            else:
                self.reply_to_user(auth[1], obj)
        else:
            if not check_user(obj.message['from_id'], self.db_session):
                self.reply_to_user('Привет! Вижу, ты впервые у нас', obj)
                self.reply_to_user(
                    'Напиши свой ник, и я тебя запомню\n'
                    'Внимание! Имя не должно начинаться или заканчиваться на цифры или недопустимые символы!',
                    obj)
                self.waiting_for_authorization = True
            else:
                self.reply_to_user('Разрабатывается', obj)

    def reply_to_user(self, text, obj):
        vk = vk_session.get_api()
        vk.messages.send(user_id=obj.message['from_id'],
                         message=text,
                         random_id=random.randint(0, 2 ** 64))


def add_user(uid, nickname, sess):
    global User
    u = User()
    u.uid = str(uid)
    u.nickname = nickname
    sess.add(u)
    sess.commit()


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


def main(vk_session, session, bot):
    longpoll = VkBotLongPoll(vk_session, group_id='212227596')

    for event in longpoll.listen():

        if event.type == VkBotEventType.MESSAGE_NEW:
            vk = vk_session.get_api()
            bot.accept_message(event.obj)


if __name__ == '__main__':
    db_session.global_init('data/db/clicker_db.sqlite')
    session = db_session.create_session()
    vk_session = vk_api.VkApi(token=TOKEN)
    bot = ClickerBot(vk_session, session)
    main(vk_session, session, bot)
