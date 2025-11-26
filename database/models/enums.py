from enum import Enum

class ProgressStatus(str, Enum):
    PLACED = "placed"
    IN_TRANSIT = "in transit"
    SHIPPED = "shipped"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"