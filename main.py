import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
from data import db_session
from data.user import User

TOKEN = 'cccf1a05dec0e26b5388dbaf2190362a2a4c2692f7aeebe98b36b2c19031ad1980136723e8bbea17879ed'




class ClickerBot:
    def __init__(self, vk_session, db_sess):
        self.vk_session = vk_session
        self.db_session = db_sess
        self.waiting_for_authorization = False # Если True, то ждет сообщения с ником для регистрации

    def accept_message(self, obj):
        if not check_user(uid=obj.message['from_id'], db_sess=self.db_session):
            self.reply_to_user('Привет! Вижу, ты впервые тут, как тебя называть?', obj)
            self.reply_to_user('Напиши свой ник:', obj)
            self.waiting_for_authorization = True
        if self.waiting_for_authorization:
            auth = check_valid_nickname(obj.message['text'])
            if auth[0]:
                add_user(obj.message['from_id'], obj.message['text'])
                self.reply_to_user('Ты зарегистрирован! удачной игры!', obj)
                self.waiting_for_authorization = False
            else:
                self.reply_to_user(auth[1], obj)
        else:
            self.reply_to_user('Бот в разработке, какая игра!?', obj)



    def reply_to_user(self, text, obj):
        vk = vk_session.get_api()
        vk.messages.send(user_id=obj.message['from_id'],
                         message=text,
                         random_id=random.randint(0, 2 ** 64))


def add_user(uid, nickname, db_sess):
    pass


def check_user(uid, db_sess):
    global User
    ids = db_sess.query(User).all()
    print(ids)
    for id in ids:
        if uid == str(ids):
            return True
    return False


def check_valid_nickname(nickname:str):
    valid = True
    reason = None
    for symbol in '''!'@#$%^&*()_+{}:"?><][';/.,'"-=`~/*\|''':
        if nickname.startswith(symbol):
            valid = False
            reason = 'Ошибка: Имя начинается с недопустимого символа!'
        if nickname.endswith(symbol):
            valid = False
            reason = 'Ошибка: Имя заканчивается на недопустимый символ!'
    for symb in '''!'^()+{}:"?';/.,'"-=`~/*\|''':
        if symb in nickname:
            valid = False
            reason = 'Ошибка: Внутри имени недопустимый символ!'
    return [valid, reason]# Возвращает подходит/не подходит, и если не подходит, то почему


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
