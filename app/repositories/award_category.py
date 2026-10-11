from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.award_category import AwardCategory
from app.models.nomination import Nomination


class AwardCategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> AwardCategory | None:
        statement = select(AwardCategory).where(AwardCategory.name == name)
        return self.db.exec(statement).one_or_none()

    def get_by_id(self, category_id: int) -> AwardCategory | None:
        return self.db.get(AwardCategory, category_id)

    def list_all(self) -> list[AwardCategory]:
        statement = select(AwardCategory).order_by(
            AwardCategory.required_hours.desc(), AwardCategory.name
        )
        return list(self.db.exec(statement).all())

    def create(self, category: AwardCategory) -> AwardCategory:
        try:
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
            return category
        except IntegrityError:
            self.db.rollback()
            raise

    def update(self, category: AwardCategory) -> AwardCategory:
        try:
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
            return category
        except IntegrityError:
            self.db.rollback()
            raise

    def has_nominations(self, category_id: int) -> bool:
        # STUDENT SNIPPET START
        # Check whether any nomination references this category.
        statement = (
            select(Nomination.id)
            .where(Nomination.category_id == category_id)
            .limit(1)
        )
        return self.db.exec(statement).first() is not None
        # STUDENT SNIPPET END

    def delete(self, category: AwardCategory) -> None:
        self.db.delete(category)
        self.db.commit()
