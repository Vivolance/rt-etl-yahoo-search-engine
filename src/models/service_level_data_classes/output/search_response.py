from pydantic import BaseModel


class SearchResponse(BaseModel):
    job_id: str
    search_term: str
