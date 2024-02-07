from dotenv import load_dotenv
import telebot
from PIL import Image, ImageEnhance, ImageFilter

import os


GREETINGS = (
    'Привет, {name}!\n'
    'Отправьте одно изображение и выберите преобразование'
)
ERROR_MANIPULATION_NAME = 'Ключ преобразования введен с ошибкой!'
UNKNOWN_ERROR = 'Неизвестная ошибка при выборе фильтра'
NOT_TOKEN = (
    'Отсутствует(ют) обязательная(ые) переменная(ые) окружения: {tokens}!\n'
    'Программа принудительно остановлена.'
)

TEMP_FILE_NAME = 'message.txt'
ENHANCES = ('Contrast',)
FILTERS = {
    'BLUR': ImageFilter.BLUR,
    'CONTOUR': ImageFilter.CONTOUR,
    'DETAIL': ImageFilter.DETAIL,
    'EDGE_ENHANCE': ImageFilter.EDGE_ENHANCE,
    'EDGE_ENHANCE_MORE': ImageFilter.EDGE_ENHANCE_MORE,
    'EMBOSS': ImageFilter.EMBOSS,
    'FIND_EDGES': ImageFilter.FIND_EDGES,
    'SHARPEN': ImageFilter.SHARPEN,
    'SMOOTH': ImageFilter.SMOOTH,
    'SMOOTH_MORE': ImageFilter.SMOOTH_MORE
}
FILTERS_DESCRIPTIONS = {
    'BLUR': 'размытие изображения',
    'CONTOUR': 'отрисовка контуров на изображении',
    'DETAIL': 'увеличение четкости деталей',
    'EDGE_ENHANCE': 'улучшение краев',
    'EDGE_ENHANCE_MORE': 'усиленное улучшение краев',
    'EMBOSS': 'перевод изображения в рельефное',
    'FIND_EDGES': 'поиск краев',
    'SHARPEN': 'заточка',
    'SMOOTH': 'сглаживание изображения',
    'SMOOTH_MORE': 'сильное сглаживание изображения'
}
ENHANCES_DESCRIPTIONS = {
    'Contrast': 'изменение контрастности изображения (!!!)',
}
TEXT_MANIPULATION = '\t- <b>{manipulation}</b> - {description}\n'


def create_message_manipulations():
    message = 'Возможные преобразования:\n'
    for manipulation in FILTERS_DESCRIPTIONS:
        text = TEXT_MANIPULATION.format(
            manipulation=manipulation,
            description=FILTERS_DESCRIPTIONS[manipulation]
        )
        message += text
    for manipulation in ENHANCES_DESCRIPTIONS:
        text = TEXT_MANIPULATION.format(
            manipulation=manipulation,
            description=ENHANCES_DESCRIPTIONS[manipulation]
        )
        message += text
    message += TEXT_MANIPULATION.format(
            manipulation='Resize',
            description='сжатие изображения (!!!)'
        )
    message += (
        '(!!!) отмечены преобразования, для которых '
        'после ключа через пробел необходимо указать число\n'
        'Для использования выбранного преобразования '
        'введите один из ключей:'
    )
    return message


MANIPULATIONS = create_message_manipulations()

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


def check_tokens():
    if not TELEGRAM_TOKEN:
        NOT_TOKEN.format(tokens=TELEGRAM_TOKEN)


check_tokens()
bot = telebot.TeleBot(TELEGRAM_TOKEN)


def send_message(chat_id, message):
    """Функция отправки сообщения в чат."""
    bot.send_message(
        chat_id,
        message,
        parse_mode='HTML'
    )


def download_file(file_id):
    """Функция скачивания присланного файла."""
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = (file_id + file_info.file_path).replace('/', '_')
    with open(filename, 'wb') as file:
        file.write(downloaded_file)
    with open(TEMP_FILE_NAME, 'w') as file:
        file.write(filename)


def filtration_image(filename, filtername, number, chat_id):
    """Функция применения преобразования к изображению."""
    source_image = Image.open(filename)
    if filtername.upper() in FILTERS:
        enhanced_image = source_image.filter(FILTERS[filtername.upper()])
        enhanced_image = enhanced_image.convert('RGB')
        enhanced_image.save(filename)
    elif filtername.lower() == 'contrast':
        enhanced_image = ImageEnhance.Contrast(source_image).enhance(number)
        enhanced_image.save(filename)
    elif filtername.lower() == 'resize':
        number = int(number)
        enhanced_image = source_image.resize(
            (
                source_image.size[0] // number,
                source_image.size[1] // number
            )
        )
        enhanced_image.save(filename)
    else:
        send_message(
            chat_id,
            ERROR_MANIPULATION_NAME
        )


@bot.message_handler(commands=['start'])
def greetings(message):
    """Функция отправки приветственного сообщения."""
    send_message(
        message.chat.id,
        GREETINGS.format(name=message.chat.first_name)
    )


@bot.message_handler(content_types=['photo'])
def get_image(message):
    """Функция получения изображения и отправки запроса фильтра."""
    file_id = message.photo[-1].file_id
    download_file(file_id)
    send_message(
        message.chat.id,
        MANIPULATIONS
    )


@bot.message_handler(content_types=['text'])
def send_manipulation_image(message):
    """Функция отправки преобразованного изображения."""
    filtername = message.text.split(' ')[0]
    if len(message.text.split(' ')) == 2:
        number = float(message.text.split(' ')[1])
    else:
        number = 1
    with open(TEMP_FILE_NAME, 'r') as file:
        text_from_file = file.readlines()
    if text_from_file:
        filename = text_from_file[0]
        filtration_image(filename, filtername, number, message.chat.id)
        image = open(filename, 'rb')
        bot.send_photo(message.chat.id, image)
        image.close()
    else:
        send_message(
            message.chat.id,
            UNKNOWN_ERROR
        )
    if os.path.exists(filename):
        os.remove(filename)
    if os.path.exists(TEMP_FILE_NAME):
        os.remove(TEMP_FILE_NAME)


def main():
    bot.polling()


if __name__ == '__main__':
    main()
