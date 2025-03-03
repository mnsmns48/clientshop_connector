from datetime import datetime
from typing import Annotated, Optional, List

from sqlalchemy import SmallInteger, TIMESTAMP, DateTime, func, UniqueConstraint, Index, Computed, text, event, \
    ForeignKey, Table, Column, Integer
from sqlalchemy.dialects.postgresql import JSON, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column, relationship

datetime_obj = Annotated[datetime, mapped_column(DateTime(timezone=False), server_default=func.now())]
info_obj = Annotated[dict, mapped_column(type_=JSON)]


class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


product_description_association_table = Table(
    "product_description_association",
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column("product_id", ForeignKey("stocktable.code")),
    Column("description_id", ForeignKey("digitaltube.id")),
    UniqueConstraint('product_id', 'description_id', name="idx_unique_product_description")
)


class StockTable(Base):
    code: Mapped[int] = mapped_column(primary_key=True)
    parent: Mapped[int]
    ispath: Mapped[bool]
    name: Mapped[str]
    quantity: Mapped[int] = mapped_column(nullable=True)
    price: Mapped[int] = mapped_column(nullable=True)
    descs: Mapped[list["DigitalTube"]] = relationship(
        secondary=product_description_association_table,
        back_populates="products")


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


class DigitalTube(Base):
    __table_args__ = (UniqueConstraint('link', name='uix_link'),
                      Index('idx_link', 'link'),
                      Index('idx_title_tsv', 'title_tsv', postgresql_using='gin'))
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    title_tsv: Mapped[TSVECTOR] = mapped_column(TSVECTOR, Computed("to_tsvector('english', title)",
                                                                   persisted=True))
    brand: Mapped[str]
    product_type: Mapped[str | None]
    link: Mapped[str]
    source: Mapped[str]
    info: Mapped[info_obj]
    pros_cons: Mapped[Optional[info_obj]]
    create: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    update: Mapped[datetime_obj]
    products: Mapped[list["StockTable"]] = relationship(
        secondary=product_description_association_table,
        back_populates="descs")


@event.listens_for(DigitalTube.__table__, 'after_create')
def create_update_title_tsv_trigger(target, connection, **kw):
    connection.execute(text(
        f"""
        CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
        ON {DigitalTube.__table__} FOR EACH ROW EXECUTE PROCEDURE
        tsvector_update_trigger(title_tsv, 'pg_catalog.english', title);
        """
    ))
