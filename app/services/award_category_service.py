from sqlalchemy.exc import IntegrityError

from app.models.award_category import AwardCategory
from app.repositories.award_category import AwardCategoryRepository


class AwardCategoryService:
    def __init__(self, repository: AwardCategoryRepository):
        self.repository = repository

    def list_categories(self) -> list[AwardCategory]:
        return self.repository.list_all()

    def get_category(self, category_id: int) -> AwardCategory | None:
        return self.repository.get_by_id(category_id)

    def create_category(
        self, name: str, description: str, required_hours: int
    ) -> AwardCategory:
        name = name.strip()
        description = description.strip()
        if not name:
            raise ValueError("Category name is required")
        if required_hours <= 0:
            raise ValueError("Required hours must be greater than zero")
        if self.repository.get_by_name(name) is not None:
            raise ValueError("A category with this name already exists")

        category = AwardCategory(
            name=name,
            description=description,
            required_hours=required_hours,
        )
        try:
            return self.repository.create(category)
        except IntegrityError as exc:
            raise ValueError("A category with this name already exists") from exc

    def update_category(
        self,
        category_id: int,
        name: str,
        description: str,
        required_hours: int,
    ) -> AwardCategory:
        category = self.repository.get_by_id(category_id)
        if category is None:
            raise ValueError("Award category not found")

        name = name.strip()
        description = description.strip()
        if not name:
            raise ValueError("Category name is required")
        if required_hours <= 0:
            raise ValueError("Required hours must be greater than zero")
        existing = self.repository.get_by_name(name)
        if existing is not None and existing.id != category_id:
            raise ValueError("A category with this name already exists")

        category.name = name
        category.description = description
        category.required_hours = required_hours
        try:
            return self.repository.update(category)
        except IntegrityError as exc:
            raise ValueError("A category with this name already exists") from exc

    def delete_category(self, category_id: int) -> None:
        # STUDENT SNIPPET START
        # Check the category and its nominations before delegating deletion.
        category = self.repository.get_by_id(category_id)
        if category is None:
            raise ValueError("Award category not found")
        if self.repository.has_nominations(category_id):
            raise ValueError(
                "This category cannot be deleted while nominations reference it."
            )
        try:
            self.repository.delete(category)
        except IntegrityError as exc:
            raise ValueError(
                "This category cannot be deleted while nominations reference it."
            ) from exc
        # STUDENT SNIPPET END
