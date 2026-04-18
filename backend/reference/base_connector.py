"""
Base connector abstract class for EchoMind.
All data connectors must inherit from this class.
"""

from abc import ABC, abstractmethod
from models.normalized_input import NormalizedInput


class BaseConnector(ABC):
    """Abstract base class for all data connectors."""
    
    @abstractmethod
    def fetch_data(self) -> list[NormalizedInput]:
        """
        Fetch data from the source and return normalized input objects.
        
        Returns:
            list[NormalizedInput]: List of normalized data objects.
        """
        pass
