from datetime import datetime
from typing import Annotated

from sqlalchemy import SmallInteger, DateTime, func
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column

datetime_obj = Annotated[datetime, mapped_column(DateTime(timezone=False), server_default=func.now())]
info_obj = Annotated[dict, mapped_column(type_=JSON)]


class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class StockTable(Base):
    code: Mapped[int] = mapped_column(primary_key=True)
    parent: Mapped[int]
    ispath: Mapped[bool]
    name: Mapped[str]
    quantity: Mapped[int] = mapped_column(nullable=True)
    price: Mapped[int] = mapped_column(nullable=True)
    info: Mapped[dict | None ] = mapped_column(type_=JSON)


class Activity(Base):
    operation_code: Mapped[int] = mapped_column(primary_key=True)
    time_: Mapped[TIMESTAMP] = mapped_column(DateTime(timezone=False))
    product_code: Mapped[int]
    product: Mapped[str]
    quantity: Mapped[int] = mapped_column(SmallInteger)
    price: Mapped[float]
    sum_: Mapped[float]
    noncash: Mapped[bool]
    return_: Mapped[bool]
