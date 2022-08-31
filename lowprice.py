from Functions import *

@bot.message_handler(commands=['lowprice'])
def lowprce(message):
    func_order(1)
    msg = bot.send_message(message.chat.id, f"{message.chat.first_name} введите город")
    bot.register_next_step_handler(msg, query)




