"""data types

Revision ID: 4829f32490be
Revises: 4829f32490bd
Create Date: 2023-06-13 13:39:44.114420

"""

import json
import os

import sqlalchemy as sa
from alembic import op

from app.models.models import ModelDataType

revision = '4829f32490be'
down_revision = '4829f32490bd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.update(ModelDataType)
               .where(ModelDataType.id == 1)
               .values(
        desc='Тип данных, значениями которого является произвольная последовательность (строка) символов алфавита. Каждая переменная такого типа может быть представлена фиксированным количеством байтов не более 1,048,576 символов')
               )

    op.execute(sa.update(ModelDataType)
    .where(ModelDataType.id == 2)
    .values(
        desc='Тип данных, значениями которого является произвольная последовательность (строка) unicode-символов. Каждая переменная такого типа имеет произвольную длину')
    )

    op.execute(sa.update(ModelDataType)
    .where(ModelDataType.id == 3)
    .values(
        desc='Примитивный тип данных, служащий для представления целых чисел')
    )

    op.execute(sa.update(ModelDataType)
    .where(ModelDataType.id == 4)
    .values(
        desc='Тип данных, содержащий числа, записанные с десятичной точкой и/или с десятичным порядком')
    )

    op.execute(sa.update(ModelDataType)
    .where(ModelDataType.id == 6)
    .values(
        desc='Дата или частичная дата (например, просто год или год + месяц), используемая в общении между людьми. Формат ГГГГ, ГГГГ-ММ или ГГГГ-ММ-ДД, например. 2018, 1973-06 или 1905-08-23. НЕ ДОЛЖНО быть смещения часового пояса. Даты ДОЛЖНЫ быть действительными датами')
    )

    op.execute(sa.update(ModelDataType)
    .where(ModelDataType.id == 8)
    .values(
        desc='Указывает, что значение берется из набора контролируемых строк, определенных в другом месте. Технически код ограничен строкой, которая имеет по крайней мере один символ и не имеет начальных или конечных пробелов, и где в содержимом нет пробелов, кроме одиночных пробелов')
    )

    op.execute(sa.update(ModelDataType)
    .where(ModelDataType.id == 9)
    .values(
        desc='Тип данных, предназначенный для хранения любых двоичных данных в виде строки в кодировке base64')
    )


def downgrade() -> None:
    pass
