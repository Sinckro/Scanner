from PIL import Image
import os
import requests
from io import BytesIO
from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import telebot
from telebot import types
import subprocess
import formatter_image
import tempfile
import requests
import zipfile
import time
import uuid

from yookassa import Configuration, Payment

Configuration.account_id = 381764678
Configuration.secret_key = 27583

TOKEN = '6425319786:AAEScENXwLGMGqKdhD3xiJwxk_DgK-aos-8'
YOOTOKEN = '401643678:TEST:9a04d188-07be-44de-8367-d4a0fce5a908'
bot = telebot.TeleBot(TOKEN)
user_balance = {'user_id': 0}
user_data = {}
form = 'pdf'
file_path = ''
cost = 0.2
current_message_number = 1
output_format = None
images_folder = 'D:/Scanner/images'


def create_pdf_from_image(image_path, pdf_path):
    image = Image.open(image_path)
    pdf = FPDF(unit="pt", format=[image.width, image.height])
    pdf.add_page()
    pdf.image(image_path, 0, 0, image.width, image.height)
    pdf.output(pdf_path, "F")


def create_archive(file_list, archive_name, folder_path):
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in file_list:
            arcname = os.path.relpath(file, folder_path)
            zipf.write(file, arcname)


def save_image_from_telegram(file_path, file_name):
    file_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_path}'
    response = requests.get(file_url)
    if response.status_code == 200:
        with open(file_name, 'wb') as file:
            file.write(response.content)
        print(f'Изображение успешно сохранено как {file_name}')
    else:
        print('Не удалось загрузить изображение')


def process_images(user_id, form, folder_path):
    true_suffix = '.' + form
    archive_name = "result.zip"
    if form == 'pdf':
        pdf_list = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".jpg") or file.endswith(".png"):
                    image_path = os.path.join(root, file)
                    try:
                        formatter_image.process_image(image_path)
                    except:
                        pass

                    pdf_path = os.path.join(root, file.replace(".jpg", ".pdf").replace(".png", ".pdf"))
                    create_pdf_from_image(image_path, pdf_path)
                    pdf_list.append(pdf_path)
                user_balance[user_id] = round(user_balance[user_id] - cost, 2)

        create_archive(pdf_list, archive_name, folder_path)

        with open(archive_name, "rb") as archive_file:
            bot.send_document(user_id, archive_file)
    else:
        file_list = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".jpg") or file.endswith(".png"):
                    with tempfile.NamedTemporaryFile(suffix=true_suffix, delete=False, mode='w', encoding='utf-8') as temp_file:
                        temp_file.write('Итоговый файл')
                    file_list.append(temp_file.name)
        temp_path = os.path.dirname(tempfile.NamedTemporaryFile().name)
        create_archive(file_list, archive_name, temp_path)

        with open(archive_name, "rb") as archive_file:
            bot.send_document(user_id, archive_file)

    for file in os.listdir(folder_path):
        os.remove(os.path.join(folder_path, file))


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if user_id not in user_balance:
        user_balance[user_id] = float(1000)

    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(types.InlineKeyboardButton('Личный кабинет', callback_data='profile'),
                 types.InlineKeyboardButton('Начать работу', callback_data='start_sending'))

    bot.send_message(user_id, "Привет! Добро пожаловать в бота.", reply_markup=keyboard)



@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.chat.id
    if message.text == '/profile':
        show_profile(user_id)
    elif message.text == '/pay':
        show_payment_options(user_id)
    elif message.text == '/support':
        show_support_options(user_id)
    elif message.text == '/info':
        show_bot_info(user_id)
    elif message.text == '/stat':
        show_statistics(user_id)
    elif message.text == '/done':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton('pdf', callback_data='pdf'),
                     types.InlineKeyboardButton('txt', callback_data='txt'),
                     types.InlineKeyboardButton('doc', callback_data='doc'),
                     types.InlineKeyboardButton('xml', callback_data='xml'))
        bot.send_message(user_id, "Выберите итоговый формат файла-результата:", reply_markup=keyboard)
    else:
        bot.send_message(user_id, "Извините, не могу обработать этот запрос.")


def show_profile(user_id):
    balance = user_balance[user_id]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('О боте', callback_data='info'))
    keyboard.add(types.InlineKeyboardButton('Статистика', callback_data='stat'))
    keyboard.add(types.InlineKeyboardButton('Поддержка', callback_data='support'))
    keyboard.add(types.InlineKeyboardButton('Пополнение баланса', callback_data='pay'))

    bot.send_message(user_id, f"Ваш баланс: {balance} руб", reply_markup=keyboard)


def show_payment_options(user_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton('100 руб', callback_data='100'),
                 types.InlineKeyboardButton('300 руб', callback_data='300'),
                 types.InlineKeyboardButton('500 руб', callback_data='500'))
    keyboard.row(types.InlineKeyboardButton('1000 руб', callback_data='1000'),
                 types.InlineKeyboardButton('1500 руб', callback_data='1500'),
                 types.InlineKeyboardButton('2000 руб', callback_data='2000'))

    bot.send_message(user_id, "Выберите сумму для пополнения:", reply_markup=keyboard)


def show_support_options(user_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Написать в поддержку', url='https://www.google.com'))
    keyboard.add(types.InlineKeyboardButton('Личный кабинет', callback_data='profile'))

    bot.send_message(user_id, "Выберите действие:", reply_markup=keyboard)


def show_bot_info(user_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Личный кабинет', callback_data='profile'))
    bot.send_message(user_id, "Это бот сканер", reply_markup=keyboard)


def show_statistics(user_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Личный кабинет', callback_data='profile'))
    bot.send_message(user_id, "Статистика...", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    global files
    if call.data in ['100', '300', '500', '1000', '1500', '2000']:
        prices = [types.LabeledPrice(label='Руб', amount = int(call.data)*100)]

        bot.send_invoice(call.message.chat.id, title='Пополнение баланса',
                         description='payment', invoice_payload='pay_add',
                         provider_token=YOOTOKEN, currency='RUB',
                         start_parameter='test_bot', prices=prices)

    elif call.data == 'profile':
        show_profile(call.message.chat.id)
    elif call.data == 'pay':
        show_payment_options(call.message.chat.id)
    elif call.data == 'info':
        show_bot_info(call.message.chat.id)
    elif call.data == 'stat':
        show_statistics(call.message.chat.id)
    elif call.data == 'support':
        show_support_options(call.message.chat.id)
    elif call.data == 'start_sending':
        bot.send_message(user_id, "Отправьте все фото. Когда закончите используйте команду /done (напишите в чат)")
    elif call.data in ['pdf', 'doc']:
        process_images(user_id, call.data, 'D:\Scanner\images')
    else:
        bot.answer_callback_query(call.id, text="Ошибка!")


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    response = requests.post('https://api.provider.com/confirm_payment', data={
        'token': YOOTOKEN,
        'payment_id': pre_checkout_query.id
    })
    if response.status_code == 200:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    else:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, error_message="Ошибка обработки оплаты")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    user_id = message.chat.id
    user_balance[user_id] = round(user_balance[user_id] + float(message.successful_payment.total_amount/100), 2)
    bot.send_message(message.from_user.id, 'Вы пополнили баланс на {} {}!'.format(message.successful_payment.total_amount/100, message.successful_payment.currency))




@bot.message_handler(content_types=['photo', 'document'])
def handle_content(message):
    user_id = message.chat.id

    if message.photo:
        file_id = message.photo[0].file_id
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path
        downloaded_file = bot.download_file(file_path)
        file_extension = file_path.split('.')[-1]
        file_name = f'{user_id}_{file_id}.{file_extension}'

        with open(os.path.join(images_folder, file_name), 'wb') as new_file:
            new_file.write(downloaded_file)

    elif (message.document and message.document.mime_type in ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']):
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path
        downloaded_file = bot.download_file(file_path)
        file_extension = file_path.split('.')[-1]
        file_name = f'{user_id}_{file_id}.{file_extension}'

        with open(os.path.join(images_folder, file_name), 'wb') as new_file:
            new_file.write(downloaded_file)
    elif message.document and message.document.mime_type == 'application/zip':
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path
        downloaded_file = bot.download_file(file_path)

        zip_data = BytesIO(downloaded_file)

        with zipfile.ZipFile(zip_data, 'r') as zip_ref:
            zip_ref.extractall(images_folder)
    else:
        bot.send_message(user_id, "Извините, не умею работать с таким форматом данных.")
        return


bot.infinity_polling(skip_pending = True)