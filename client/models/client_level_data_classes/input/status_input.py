from pydantic import BaseModel


class StatusInput(BaseModel):
    job_id: str
