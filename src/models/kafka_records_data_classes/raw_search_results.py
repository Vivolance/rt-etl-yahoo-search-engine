from datetime import datetime

from pydantic import BaseModel, field_serializer, field_validator

from src.models.dto_data_classes.raw_search_results_dto import RawSearchResultsDTO
from src.models.kafka_records_data_classes.raw_search_terms import RawSearchTermsRecord


class RawSearchResultsRecord(BaseModel):
    user_id: str
    search_term: str
    job_id: str
    job_created_at: datetime
    raw_search_results_id: str
    raw_search_at: datetime

    """
    cls in Pydantic validators: The cls argument in a field validator refers 
    to the class that is being validated. This method is called directly by the class,
    This allows the method to access class-level information if necessary 
    (similar to how it would work in a class method). However, Pydantic doesn't 
    require @classmethod because the validator is automatically treated like a 
    class-level method during the validation process.
    """
    @field_serializer("job_created_at")
    def serialize_job_created_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%dT%H:%M:%S")

    @field_validator("job_created_at", mode="before")
    def deserialize_job_created_at(cls, value: str | datetime) -> datetime:
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        return value

    @field_serializer("raw_search_at")
    def serialize_raw_search_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%dT%H:%M:%S")

    @field_validator("raw_search_at", mode="before")
    def deserialize_raw_search_at(cls, value: str | datetime) -> datetime:
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        return value

    @staticmethod
    def create_from_raw_search_term_and_results(
        input_record: RawSearchTermsRecord, output_record: RawSearchResultsDTO
    ) -> "RawSearchResultsRecord":
        return RawSearchResultsRecord(
            user_id=input_record.user_id,
            search_term=input_record.search_term,
            job_id=input_record.job_id,
            job_created_at=input_record.job_created_at,
            raw_search_results_id=output_record.id,
            raw_search_at=output_record.created_at,
        )
