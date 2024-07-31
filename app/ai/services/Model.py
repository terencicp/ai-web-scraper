from abc import ABC, abstractmethod


class Model(ABC):
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def input_token_cost(self) -> float:
        pass

    @property
    @abstractmethod
    def output_token_cost(self) -> float:
        pass

    @property
    @abstractmethod
    def image_cost(self) -> float:
        pass
