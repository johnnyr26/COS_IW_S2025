from abc import ABC, abstractmethod
from shared.types.spot_price import Spot_Price
from mypy_boto3_ec2.literals import InstanceTypeType
from datetime import datetime

class Virtual_Machine(ABC):
    @abstractmethod
    def get_spot_price_history(  
            self,           
            vm_type: str | InstanceTypeType,
            start_time: datetime,
            end_time: datetime,
            region: str | None
        ) -> list[Spot_Price] | None:
        pass

    @abstractmethod
    def get_spot_price(
        self,
        vm_type: str | InstanceTypeType,
        region: str | None,
    ) -> Spot_Price | None:
        pass