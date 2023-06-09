import requests

from typing import Iterable

from app.schemas.comment import CommentOut
from app.config import settings


def get_authors_data_by_guids(guids: Iterable[str], token: str) -> dict[str, dict[str, str]]:
    response = requests.get(
        f'{settings.api_iam}/internal/users/',
        json={'guids': tuple(guids)},
        headers={"Authorization": f"Bearer {token}"}
    )
    authors_data = response.json()
    return authors_data


def set_author_data(comments: Iterable[CommentOut], authors_data: dict[str, dict[str, str]]):
    for comment in comments:
        comment.author_first_name = authors_data[comment.author_guid]['first_name']
        comment.author_last_name = authors_data[comment.author_guid]['last_name']
        comment.author_middle_name = authors_data[comment.author_guid]['middle_name']
        comment.author_email = authors_data[comment.author_guid]['email']
