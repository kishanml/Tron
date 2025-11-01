from pydantic import BaseModel,Field


class CodeSummmary(BaseModel):

    code_summary: str = Field(description="code summary")
