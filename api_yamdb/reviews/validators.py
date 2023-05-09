import datetime as dt

from django.core.exceptions import ValidationError


def year_validator(value):
    if value > dt.datetime.now().year:
        raise ValidationError(
            f"год {value} не может быть больше текущего",
            params={"value": value},
        )
