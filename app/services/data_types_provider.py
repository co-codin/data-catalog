import json, os

from sqlalchemy import select, func

from app.database import db_session
from app.models.model import ModelDataType


def read_json(file_name: str):
    with open(os.getcwd() + '/app/services/data_types_provider_source/' + file_name) as f:
        data = json.load(f),

    return data


def read_xml(file_name: str):
    with open(os.getcwd() + '/app/services/data_types_provider_source/' + file_name) as f:
        data = f.read()

    return data


async def fill_table():
    async with db_session() as session:
        model_data_type = await session.execute(
            select(func.count())
            .select_from(ModelDataType)
        )
        model_data_type_count: int = model_data_type.scalar()

        if model_data_type_count == 0:
            dataset = [
                dict(
                    name='Строка',
                    desc='Тип данных, значениями которого является произвольная последовательность (строка) символов алфавита. Каждая переменная такого типа может быть представлена фиксированным количеством байтов не более 1,048,576 символов.',
                    json=read_json('string.profile.json'),
                    xml=read_xml('string.profile.xml')
                ),
                dict(
                    name='Текст',
                    desc='Тип данных, значениями которого является произвольная последовательность (строка) символов алфавита. Каждая переменная такого типа имеет произвольную длину.'
                ),
                dict(
                    name='Целое число',
                    desc='Примитивный тип данных, служащий для представления целых чисел',
                ),
                dict(
                    name='Вещественное число',
                ),
                dict(
                    name='Логический тип',
                    desc='Примитивный тип данных, принимающий два возможных значения, называемых истиной (true) и ложью (false)',
                    json=read_json('boolean.profile.json'),
                    xml=read_xml('boolean.profile.xml')
                ),
                dict(
                    name='Дата',
                    desc='Дата или частичная дата (например, просто год или год + месяц), используемая в общении между людьми. Формат ГГГГ, ГГГГ-ММ или ГГГГ-ММ-ДД, например. 2018, 1973-06 или 1905-08-23. НЕ ДОЛЖНО быть смещения часового пояса. Даты ДОЛЖНЫ быть действительными датами.',
                    json=read_json('date.profile.json'),
                    xml=read_xml('date.profile.xml')
                ),
                dict(
                    name='Дата и время',
                    desc='Дата, дата-время или неполная дата (например, только год или год + месяц), используемые в человеческом общении. Формат: ГГГГ, ГГГГ-ММ, ГГГГ-ММ-ДД или ГГГГ-ММ-ДДThh:mm:ss+zz:zz, например. 2018, 1973-06, 1905-08-23, 2015-02-07T13:28:17-05:00 или 2017-01-01T00:00:00.000Z. Если указаны часы и минуты, смещение часового пояса ДОЛЖНО быть заполнено. Фактические коды часовых поясов могут быть отправлены с использованием расширения кода часового пояса, если это необходимо. Секунды должны быть предоставлены из-за ограничений типа схемы, но могут быть заполнены нулями и могут быть проигнорированы по усмотрению получателя. Миллисекунды необязательно разрешены. Даты ДОЛЖНЫ быть действительными датами. Время «24:00» не допускается. Високосные секунды разрешены',
                    json=read_json('datetime.profile.json'),
                    xml=read_xml('datetime.profile.xml')
                ),
                dict(
                    name='Код',
                    desc='Указывает, что значение берется из набора контролируемых строк, определенных в другом месте. Технически код ограничен строкой, которая имеет по крайней мере один символ и не имеет начальных или конечных пробелов, и где в содержимом нет пробелов, кроме одиночных пробелов.',
                    json=read_json('code.profile.json'),
                    xml=read_xml('code.profile.xml')
                ),
                dict(
                    name='Двоичный тип',
                ),
                dict(
                    name='Ресурс',
                    desc='Базовый абстрактный тип для представления всех типов, содержащихся в модели',
                    json=json.loads('{}'),
                    xml='<xml>'
                ),
            ]

            for data in dataset:
                model_data_type = ModelDataType(
                    **data
                )

                session.add(model_data_type)
                await session.commit()
