from decimal import Decimal
from datetime import datetime


class Log:
    def __init__(
        self,
        id: int,
        start_time: str,
        end_time: str,
        virtual_machine: str,
        # for the given timeframe.
        num_uploads: int,
        total_uploads: int,
        cost: Decimal,
        total_cost: Decimal,
    ):
        self.id = id
        self.start_time = start_time
        self.end_time = end_time
        self.virtual_machine = virtual_machine
        self.num_uploads = num_uploads
        self.total_uploads = total_uploads

        self.cost = cost
        self.total_cost = total_cost

    def to_dict(self) -> dict[str, int | str | datetime | Decimal]:
        return {
            "id": self.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "virtual_machine": self.virtual_machine,
            "num_uploads": self.num_uploads,
            "total_uploads": self.total_uploads,
            "cost": self.cost,
            "total_cost": self.total_cost,
        }

    def __repr__(self):
        return f"""
            [id: {self.id}, start_time: {self.start_time}, end_time: {self.end_time}, vm: {self.virtual_machine}, num_uploads: {self.num_uploads}, total_uploads: {self.total_uploads}, cost: {self.cost}, total_cost: {self.total_cost}]
        """
