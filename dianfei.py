# python3

"""
Check the electricity bill of BUPT dormitory.
Help you to avoid the power shutdown.
The Cookies of https://webapp.bupt.edu.cn is needed.

Don't use my token below, it is really easy to get a Telegram Bot Token
via @BotFather
"""

from telegram.ext import Updater, Job, CommandHandler, MessageHandler, Filters, JobQueue
from telegram.bot import Bot
from telegram.update import Update

from typing import List
from datetime import time

import logging
import sys
import re

import requests

TOKEN = '426719489:AAHMwm2TVWUK58kQS_LvnnF5lNDDc-eSUMU'


class ChadianfeiService:
    headers = {
        'Pragma': 'no-cache',
        'Origin': 'https://webapp.bupt.edu.cn',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.6,en-US;q=0.4,en;q=0.2,ja;q=0.2',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Cache-Control': 'no-cache',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Referer': 'https://webapp.bupt.edu.cn/w_dianfei.html',
    }

    @staticmethod
    def query(cookies: dict = None, partment_id: str = '', floor_number: str = '', drom_number: str = '') -> (
            bool, str):

        if cookies is None:
            return False, 'Cookie is not set!'

        if partment_id == '' or partment_id.isspace():
            return False, 'Partment Id is not set'

        if floor_number == '' or floor_number.isspace():
            return False, 'Floor id is not set'

        if not floor_number.isnumeric():
            return False, 'Floor must be Number'

        if drom_number == '' or drom_number.isspace():
            return False, 'Drom Number is not set'

        data = [
            ('partmentId', partment_id),
            ('floorId', floor_number),
            ('dromNumber', drom_number),
        ]

        try:
            res = requests.post('https://webapp.bupt.edu.cn/w_dianfei/default/search',
                                headers=ChadianfeiService.headers,
                                cookies=cookies,
                                data=data)
            json_data = res.json()
        except:
            return False, sys.exc_info()[0]

        if json_data['success'] is not True:
            return False, str(json_data)
        else:
            return True, str(json_data['data']['surplus'])


def main():
    def start(bot: Bot, update: Update):
        if len(dispatcher.handlers[0]) <= 1:
            handlers = [
                CommandHandler('cookies', cookies, pass_args=True, pass_chat_data=True),
                CommandHandler('partment_id', partment_id, pass_args=True, pass_chat_data=True),
                CommandHandler('floor_number', floor_number, pass_args=True, pass_chat_data=True),
                CommandHandler('drom_number', drom_number, pass_args=True, pass_chat_data=True),
                CommandHandler('chadianfei', chadianfei, pass_chat_data=True),
                CommandHandler('poll_dianfei', poll_electricity_command_handler, pass_job_queue=True,
                               pass_chat_data=True),
                CommandHandler('cancel_poll', cancel_poll, pass_chat_data=True),
                CommandHandler('revoke_cookies_and_partment_id', revoke_cookies_and_partment_id, pass_chat_data=True),
                CommandHandler('poll_time', poll_time, pass_chat_data=True, pass_args=True),
                MessageHandler(Filters.text | Filters.command, buyao_tiaoxi)
            ]

            for command_handler in handlers:
                dispatcher.add_handler(command_handler)

        print(dispatcher.handlers)

        update.message.reply_text('''
        Hello, This is the BUPT electricity checking bot!
        Please use /cookies tell me the Cookies of https://webapp.bupt.edu.cn/w_dianfei.html first''')

    def cookies(bot: Bot, update: Update, args: List[str], chat_data: dict):
        chat_data['cookies'] = args
        update.message.reply_text('''
        Cookies set!
        Please tell me the partment ID''')

    def partment_id(bot: Bot, update: Update, args: List[str], chat_data: dict):
        if len(args) > 1:
            update.message.reply_text('Args can only be 1')
        else:
            chat_data['partment_id'] = args[0]
            update.message.reply_text('''
            Partment ID set!
            Please tell me the floor number''')

    def floor_number(bot: Bot, update: Update, args: List[str], chat_data: dict):
        if len(args) > 1:
            update.message.reply_text('Args can only be 1')
        elif not args[0].isnumeric():
            update.message.reply_text('Args can only be number')
        else:
            chat_data['floor_number'] = args[0]
            update.message.reply_text('''
            Floor Number set!
            Please tell me the drom number''')

    def drom_number(bot: Bot, update: Update, args: List[str], chat_data: dict):
        if len(args) > 1:
            update.message.reply_text('Args can only be 1')
        elif re.match('\d-\d{3}', args[0]) is None:
            update.message.reply_text('Args must be as 3-311')
        else:
            chat_data['drom_number'] = args[0]
            update.message.reply_text('''
            Drom Number set!
            You could chadianfei via /chadianfei''')

    def chadianfei(bot: Bot, update: Update, chat_data: dict):

        cookies_local = {}

        for cookie in chat_data['cookies']:
            cookie_pair = cookie.split(':')
            cookies_local[cookie_pair[0]] = cookie_pair[1]

        success, message = ChadianfeiService.query(cookies_local, chat_data['partment_id'], chat_data['floor_number'],
                                                   chat_data['drom_number'])

        if success:
            update.message.reply_text('Success, ' + message + ' kwh left')
        else:
            update.message.reply_text('Fail, ' + message)

    def buyao_tiaoxi(bot: Bot, update: Update):
        update.message.reply_text('Only 查电费，not 调戏！！')

    def poll_electricity_bill(bot: Bot, job: Job):
        context = job.context

        chat_data = context['chat_data']
        chat_id = context['chat_id']

        cookies_local = {}

        for cookie in chat_data['cookies']:
            cookie_pair = cookie.split(':')
            cookies_local[cookie_pair[0]] = cookie_pair[1]

        success, message = ChadianfeiService.query(cookies_local, chat_data['partment_id'], chat_data['floor_number'],
                                                   chat_data['drom_number'])
        if success:
            left_kwh = float(message)

            if left_kwh < 30.0:
                bot.send_message(chat_id=chat_id, text='''
                Your dianfei is less than 30 kwh.
                Please charge dianfei!!!
                ''')
        else:
            bot.send_message(chat_id=chat_id, text='Fail' + message)

    def poll_electricity_command_handler(bot: Bot, update: Update, job_queue: JobQueue, chat_data: dict):
        context = {
            'chat_data': chat_data,
            'chat_id': update.message.chat_id
        }

        if 'polling_time' in chat_data:
            polling_time = chat_data['polling_time']
        else:
            polling_time = time(8, 0, 0)

        job = job_queue.run_daily(poll_electricity_bill, time=polling_time, context=context)
        chat_data['job'] = job

        update.message.reply_text('Poll dianfei per day!')

    def cancel_poll(bot: Bot, update: Update, chat_data: dict):
        if 'job' not in chat_data:
            update.message.reply_text('You have not polling job')
        else:
            job: Job = chat_data['job']
            job.schedule_removal()
            del chat_data['job']
            update.message.reply_text('Successfully cancel polling')

    def poll_time(bot: Bot, update:Update, args: List[str], chat_data:dict):
        if len(args) != 1 or ':' not in args[0]:
            update.message.reply_text('Usage /poll_time h:mm:ss')
        elif 'job' in chat_data:
            update.message.reply_text('You have polling job, cancel it first!')
        else:
            h_m_s = args[0].split(':')
            chat_data['polling_time'] = time(int(h_m_s[0]), int(h_m_s[1]), int(h_m_s[2]))

    def revoke_cookies_and_partment_id(bot: Bot, update: Update, chat_data: dict):
        if 'cookies' in chat_data:
            del chat_data['cookies']

        if 'partment_id' in chat_data:
            del chat_data['partment_id']

        update.message.reply_text('Revoke successfully!')

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    start_command_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_command_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()
