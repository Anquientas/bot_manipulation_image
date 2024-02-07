from dotenv import load_dotenv
import telebot
from PIL import Image, ImageEnhance, ImageFilter

import os


load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


def check_tokens():
    if not TELEGRAM_TOKEN:
        NOT_TOKEN.format(tokens=TELEGRAM_TOKEN)


check_tokens()
bot = telebot.TeleBot(TELEGRAM_TOKEN)


FOLDER = 'download_files'
PATH = os.getcwd() + '\\' + FOLDER + '\\'
TEMP_FILE_NAME = PATH + '{name}_temp_filename.txt'

ENHANCES = ('contrast', 'resize')
FILTERS = {
    'blur': ImageFilter.BLUR,
    'contour': ImageFilter.CONTOUR,
    'detail': ImageFilter.DETAIL,
    'edge_enhance': ImageFilter.EDGE_ENHANCE,
    'edge_enhance_more': ImageFilter.EDGE_ENHANCE_MORE,
    'emboss': ImageFilter.EMBOSS,
    'find_edges': ImageFilter.FIND_EDGES,
    'sharpen': ImageFilter.SHARPEN,
    'smooth': ImageFilter.SMOOTH,
    'smooth_more': ImageFilter.SMOOTH_MORE
}

GREETINGS = (
    'Привет, {name}!\n'
    'Отправьте одно изображение и выберите преобразование'
)
ERROR_MANIPULATION_NAME = 'Ключ преобразования введен с ошибкой!'
ERROR_NUMBER = (
    'После ключа не было введено число! Преобразование не выполнено!'
)
UNKNOWN_ERROR = (
    'Неизвестная ошибка при подготовке и отправке преобразованного изображения'
)
UNKNOWN_ERROR_MANIPULATION = 'Неизвестная ошибка при произведении манипуляции'
NOT_TOKEN = (
    'Отсутствует(ют) обязательная(ые) переменная(ые) окружения: {tokens}!\n'
    'Программа принудительно остановлена.'
)
MANIPULATION_TEXT = '<b>{manipulation}</b> - {description}\n'
MANIPULATION_DESCRIPTIONS = {
    'Blur': 'размытие изображения',
    'Contour': 'отрисовка контуров на изображении',
    'Detail': 'увеличение четкости деталей',
    'Edge_enhance': 'улучшение краев (просто перевод)',
    'Edge_enhance_more': 'усиленное улучшение краев (просто перевод)',
    'Emboss': 'перевод изображения в рельефное',
    'Find_edges': 'поиск краев (просто перевод)',
    'Sharpen': 'заточка (просто перевод)',
    'Smooth': 'сглаживание изображения',
    'Smooth_more': 'сильное сглаживание изображения',
    'Contrast': 'изменение контрастности изображения (число)',
    'Resize': 'сжатие изображения (целое положительное число больше единицы)',
}


def create_message_manipulations():
    message = 'Возможные преобразования:\n'
    for manipulation in MANIPULATION_DESCRIPTIONS:
        text = MANIPULATION_TEXT.format(
            manipulation=manipulation,
            description=MANIPULATION_DESCRIPTIONS[manipulation]
        )
        message += text
    message += (
        'Заметкой "(число)" отмечены преобразования, для которых '
        'после ключа через пробел необходимо указать число\n\n'
        'Для использования выбранного преобразования '
        'введите один из ключей:'
    )
    return message


MANIPULATIONS_TEXT = create_message_manipulations()


def create_folder_for_files():
    """Функция создания папки временных файлов и предварительной очистки."""
    if FOLDER not in os.listdir(path='.'):
        os.mkdir(FOLDER)
    else:
        for file in os.listdir(path=PATH):
            os.remove(PATH + file)


def send_message(chat_id, message):
    """Функция отправки сообщения в чат."""
    bot.send_message(
        chat_id,
        message,
        parse_mode='HTML'
    )


def download_file(file_id, user_first_name):
    """Функция скачивания присланного файла."""
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = (
        user_first_name + file_id + file_info.file_path
    ).replace('/', '_')
    with open(PATH + filename, 'wb') as file:
        file.write(downloaded_file)
    with open(TEMP_FILE_NAME.format(name=user_first_name), 'w') as file:
        file.write(PATH + filename)


def manipulation_image(filename, filtername, number, chat_id):
    """Функция применения преобразования к изображению."""
    source_image = Image.open(filename)
    if filtername in FILTERS:
        enhanced_image = source_image.filter(FILTERS[filtername])
        enhanced_image = enhanced_image.convert('RGB')
        enhanced_image.save(filename)
    elif number == 0:
        send_message(
            chat_id,
            ERROR_NUMBER
        )
    elif filtername == 'contrast':
        enhanced_image = ImageEnhance.Contrast(source_image).enhance(number)
        enhanced_image.save(filename)
    elif filtername == 'resize':
        number = abs(int(number))
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
            UNKNOWN_ERROR_MANIPULATION
        )


def check_manipulation(message):
    """Функция проверки содержимого сообщения."""
    parts = message.text.split(' ')
    if len(parts) > 2 or len(parts) == 0:
        return None, None
    if len(parts) == 2:
        first_part = parts[0].lower()
        if first_part in FILTERS or first_part in ENHANCES:
            for file in os.listdir(path=PATH):
                if file.startswith(message.chat.first_name):
                    return first_part, float(parts[1].replace(',', '.'))
        return None, None
    return message.text.split(' ')[0], 0


def read_filename(user_first_name):
    """Функция считывания названия файла изображения из временного файла."""
    with open(
        TEMP_FILE_NAME.format(name=user_first_name),
        'r'
    ) as file:
        text_from_file = file.readlines()
    if text_from_file:
        return text_from_file[0]
    else:
        return None


def check_file(file):
    """Функция проверки наличия файла."""
    return os.path.exists(file)


def delete_temp_files(user_first_name, chat_id):
    """Функция удаления временных файлов и отправки результатов."""
    if check_file(TEMP_FILE_NAME.format(name=user_first_name)):
        filename = read_filename(user_first_name)
        os.remove(TEMP_FILE_NAME.format(name=user_first_name))
        if filename:
            if check_file(filename):
                with open(filename, 'rb') as image:
                    bot.send_photo(chat_id, image)
                os.remove(filename)
    else:
        for file in os.listdir(path=PATH):
            if file.startswith(user_first_name):
                os.remove(file)


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
    download_file(file_id, message.chat.first_name)
    send_message(
        message.chat.id,
        MANIPULATIONS_TEXT
    )


@bot.message_handler(content_types=['text'])
def send_manipulation_image(message):
    """Функция отправки преобразованного изображения."""
    manipulation_name, number = check_manipulation(message)
    if (
            manipulation_name and
            check_file(TEMP_FILE_NAME.format(name=message.chat.first_name))
       ):
        filename = read_filename(message.chat.first_name)
        if filename:
            manipulation_image(
                filename,
                manipulation_name.lower(),
                number,
                message.chat.id
            )
        else:
            send_message(
                message.chat.id,
                UNKNOWN_ERROR
            )
    else:
        send_message(
            message.chat.id,
            ERROR_MANIPULATION_NAME
        )
        greetings(message)

    delete_temp_files(
        message.chat.first_name,
        message.chat.id
    )


def main():
    bot.polling(interval=5)


if __name__ == '__main__':
    create_folder_for_files()
    main()
