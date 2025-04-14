from datetime import datetime
from mypy_boto3_ec2.literals import InstanceTypeType

class Spot_Price():
    def __init__(
            self, 
            vm_type: str | InstanceTypeType, 
            price: float,
            timestamp: datetime
        ):
            self.vm_type = vm_type
            self.price = price
            self.timestamp = timestamp

        
    def __repr__(self):
          return f"VM Type: {self.vm_type}, Price: {self.price}, Timestamp: {self.timestamp}"
    
    def __lt__(self, other: "Spot_Price") -> bool:
        return self.price < other.price