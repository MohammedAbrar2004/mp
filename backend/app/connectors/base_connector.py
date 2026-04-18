from typing import List
from models.normalized_input import NormalizedInput


class BaseConnector:
    def fetch(self) -> List[NormalizedInput]:
        raise NotImplementedError
