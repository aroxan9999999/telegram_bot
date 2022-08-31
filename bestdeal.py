from Functions import *
import csv
from datetime import datetime

@bot.message_handler(commands=['bestdeal'])
def bestdeal(message):
    func_order(3)
    msg = bot.send_message(message.chat.id, f"{message.chat.first_name} введите город")
    bot.register_next_step_handler(msg, query)





