from pydantic import BaseModel


class ResultInput(BaseModel):
    job_id: str
