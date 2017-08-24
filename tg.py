# encoding: utf-8

"""
@author: h3l
@contact: xidianlz@gmail.com
@file: tg.py
@time: 2017/8/22 16:32
"""
from html import unescape
from urllib.parse import urlparse, parse_qs
import subprocess

import telegram
from telegram.error import BadRequest
from telegram.utils.request import Request
from telegram.ext import Updater
from telegram.ext import CommandHandler, MessageHandler, Filters

import itchat
from itchat.content import *

# 申请telegram后获得的bot token
TELEGRAM_BOT_TOKEN = "need to fill"
CHAT_ID = None
SUB_SECRET = "SUB SECRET"
# 转发消息的群名, 直接复制就好
GROUP_WHITELIST = []
ALL_GROUP = True
# 要用代理啊，不然连不到telegram服务器啊
HTTP_PROXY = "http://127.0.0.1:1087"


bot_instance = telegram.Bot(token=TELEGRAM_BOT_TOKEN,
                            request=Request(proxy_url=HTTP_PROXY))

update_instance = Updater(bot=bot_instance)


def check_is_myself(msg):
    if msg.User.UserName == "filehelper":
        return False
    return msg.FromUserName == itchat.originInstance.storageClass.userName


def get_name(msg):
    if hasattr(msg.User, "NickName"):
        name = msg.User.NickName
    else:
        name = msg.User.UserName
    return name


@itchat.msg_register([TEXT], isFriendChat=True)
def forward_personal_text(msg):
    global CHAT_ID
    name = get_name(msg)
    if not check_is_myself(msg):
        bot_instance.send_message(CHAT_ID,
                                  "[{name}]({url}) : {content}".format(
                                      name=name,
                                      url="http://google.com?user={}".format(msg["FromUserName"]),
                                      content=msg.Content),
                                  parse_mode="Markdown"
                                  )


@itchat.msg_register(TEXT, isGroupChat=True)
def forward_group_text(msg):
    global CHAT_ID
    if not check_is_myself(msg):
        group_name = unescape(msg.User.NickName)
        if not ALL_GROUP:
            if group_name not in GROUP_WHITELIST:
                return None
        bot_instance.send_message(CHAT_ID,
                                  "[{group}]({url})—[{user}]({url}) : {content}".format(
                                      group=group_name,
                                      url="http://google.com?user={}".format(msg["FromUserName"]),
                                      user=msg.ActualNickName,
                                      content=msg.Content),
                                  parse_mode="Markdown"
                                  )


@itchat.msg_register([PICTURE], isFriendChat=True, isGroupChat=True)
def forward_pic(msg):
    global CHAT_ID
    name = get_name(msg)
    if not check_is_myself(msg):
        if hasattr(msg, "IsAt"):
            if not ALL_GROUP:
                if unescape(name) not in GROUP_WHITELIST:
                    return None
            name += "—{}".format(msg.ActualNickName)
        bot_instance.send_message(CHAT_ID,
                                  "[{name}]({url}) 发送了图片, loading~".format(
                                      name=name,
                                      url="http://google.com?user={}".format(msg["FromUserName"])
                                  ),
                                  parse_mode="Markdown"
                                  )
        # save img
        msg.Text(msg['FileName'])
        try:
            bot_instance.send_photo(CHAT_ID, photo=open('./{}'.format(msg['FileName']), 'rb'))
        except BadRequest:
            pass
        finally:
            subprocess.Popen("rm ./{}".format(msg['FileName']), shell=True)


def sub(bot, update):
    global CHAT_ID
    if update.message.text.split(maxsplit=1)[-1] == SUB_SECRET:
        CHAT_ID = update.message.chat_id
        update.message.reply_text("sub success")


def toggle(bot, update):
    global ALL_GROUP
    ALL_GROUP = not ALL_GROUP
    update.message.reply_text("success, {}".format("receive all" if ALL_GROUP else "filtered"))


def echo(bot, update):
    url = update.message["reply_to_message"]["entities"][0]["url"]
    qs = urlparse(url).query
    target = parse_qs(qs)["user"][0]
    if update.message.text:
        try:
            reply_content = update.message["text"]
            itchat.send_msg(reply_content, target)
        except Exception as e:
            print(e)
    elif update.message.photo:
        new_file = bot.get_file(update.message.photo[-1].file_id)
        print(update.message.photo[-1].file_id)
        new_file.download('tmp.jpg')
        itchat.send_image('tmp.jpg', target)
        subprocess.Popen("rm ./{}".format("tmp.jpg"), shell=True)


dis = update_instance.dispatcher
sub_handler = CommandHandler("sub", sub)
toggle_handler = CommandHandler("t", toggle)
message_handler = MessageHandler(Filters.text | Filters.photo, echo)
dis.add_handler(sub_handler)
dis.add_handler(toggle_handler)
dis.add_handler(message_handler)
update_instance.start_polling()
itchat.auto_login(True)
itchat.run(True)
