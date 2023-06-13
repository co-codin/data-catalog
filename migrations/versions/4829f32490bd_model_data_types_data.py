"""data types

Revision ID: 4829f32490bd
Revises: 4829f32490bc
Create Date: 2023-06-13 13:39:44.114420

"""

import os, json
from alembic import op
import sqlalchemy as sa

from app.models.models import ModelDataType


revision = '4829f32490bd'
down_revision = '4829f32490bc'
branch_labels = None
depends_on = None

def read_json(file_name: str):
    with open(os.getcwd() + '/migrations/data_types_provider_source/' + file_name) as f:
        data = json.load(f),

    return data


def read_xml(file_name: str):
    with open(os.getcwd() + '/migrations/data_types_provider_source/' + file_name) as f:
        data = f.read()

    return data


def upgrade() -> None:
    model_data_type = op.execute(
        sa.select(sa.func.count())
        .select_from(ModelDataType)
    )
    
    if not model_data_type is None:
        model_data_type_count: int = model_data_type.scalar()
        if model_data_type_count != 0:
            op.execute(
                sa.delete(ModelDataType)
                .where(ModelDataType.id <= 10)
            )
        
        
    dataset = [
        dict(
            id=1,
            name='Строка',
            desc='Тип данных, значениями которого является произвольная последовательность (строка) символов алфавита. Каждая переменная такого типа может быть представлена фиксированным количеством байтов не более 1,048,576 символов.',
            json=read_json('string.profile.json'),
            xml=read_xml('string.profile.xml')
        ),
        dict(
            id=2,
            name='Текст',
            desc='Тип данных, значениями которого является произвольная последовательность (строка) unicode-символов. Каждая переменная такого типа имеет произвольную длину.',
            json=read_json('markdown.profile.json'),
            xml=read_xml('markdown.profile.xml')
        ),
        dict(
            id=3,
            name='Целое число',
            desc='Примитивных тип данных, служащий для представления целых чисел.',
            json=read_json('integer.profile.json'),
            xml=read_xml('integer.profile.xml')
        ),
        dict(
            id=4,
            name='Вещественное число',
            desc='Тип данных, содержащий числа, записанные с десятичной точкой и/или с десятичным порядком.',
            json=read_json('decimal.profile.json'),
            xml=read_xml('decimal.profile.xml')
        ),
        dict(
            id=5,
            name='Логический тип',
            desc='Примитивный тип данных, принимающий два возможных значения, называемых истиной (true) и ложью (false)',
            json=read_json('boolean.profile.json'),
            xml=read_xml('boolean.profile.xml')
        ),
        dict(
            id=6,
            name='Дата',
            desc='Дата или частичная дата (например, просто год или год + месяц), используемая в общении между людьми. Формат ГГГГ, ГГГГ-ММ или ГГГГ-ММ-ДД, например. 2018, 1973-06 или 1905-08-23. НЕ ДОЛЖНО быть смещения часового пояса. Даты ДОЛЖНЫ быть действительными датами.',
            json=read_json('date.profile.json'),
            xml=read_xml('date.profile.xml')
        ),
        dict(
            id=7,
            name='Дата и время',
            desc='Дата, дата-время или неполная дата (например, только год или год + месяц), используемые в человеческом общении. Формат: ГГГГ, ГГГГ-ММ, ГГГГ-ММ-ДД или ГГГГ-ММ-ДДThh:mm:ss+zz:zz, например. 2018, 1973-06, 1905-08-23, 2015-02-07T13:28:17-05:00 или 2017-01-01T00:00:00.000Z. Если указаны часы и минуты, смещение часового пояса ДОЛЖНО быть заполнено. Фактические коды часовых поясов могут быть отправлены с использованием расширения кода часового пояса, если это необходимо. Секунды должны быть предоставлены из-за ограничений типа схемы, но могут быть заполнены нулями и могут быть проигнорированы по усмотрению получателя. Миллисекунды необязательно разрешены. Даты ДОЛЖНЫ быть действительными датами. Время «24:00» не допускается. Високосные секунды разрешены',
            json=read_json('datetime.profile.json'),
            xml=read_xml('datetime.profile.xml')
        ),
        dict(
            id=8,
            name='Код',
            desc='Указывает, что значение берется из набора контролируемых строк, определенных в другом месте. Технически код ограничен строкой, которая имеет по крайней мере один символ и не имеет начальных или конечных пробелов, и где в содержимом нет пробелов, кроме одиночных пробелов.',
            json=read_json('code.profile.json'),
            xml=read_xml('code.profile.xml')
        ),
        dict(
            id=9,
            name='Двоичный тип',
            desc='Тип данных, предназначенный для хранения любых двоичных данных в виде строки в кодировке base64.',
            json=read_json('code.profile.json'),
            xml=read_xml('code.profile.xml')
        ),
        dict(
            id=10,
            name='Ресурс',
            desc='Базовый абстрактный тип для представления всех типов, содержащихся в модели',
            json=json.loads('{}'),
            xml='<xml>'
        ),
    ]

    for data in dataset:
        op.execute(sa.insert(ModelDataType).values(
            id=data['id'],
            name=data['name'],
            desc=data['desc'],
            json=data['json'],
            xml=data['xml']
        ))


def downgrade() -> None:
    pass
