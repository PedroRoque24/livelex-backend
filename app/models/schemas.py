from pydantic import BaseModel
from typing import List

class FileList(BaseModel):
    files: List[str]

class Patients(BaseModel):
    patients: List[str]

class Cases(BaseModel):
    cases: List[str]
