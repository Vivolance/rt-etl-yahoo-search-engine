from pydantic import BaseModel


class SearchInput(BaseModel):
    search_term: str
    user_id: str
