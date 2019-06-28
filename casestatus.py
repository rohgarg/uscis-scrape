from enum import Enum

class CaseStatus(Enum):
  UNKNOWN = 0,
  RECEIVED = 1,
  APPROVED = 2,
  NEW_CARD = 3,
  MAILED = 4,
  USPS_PICKED = 5,
  DELIVERED = 6,

  def __str__(self):
    return str(self.name)
  
  def __repr__(self):
    return str(self.name)

  @classmethod
  def csv_to_status(self, input):
    if "RECEIVED" in input:
      return CaseStatus.RECEIVED
    elif "APPROVED" in input:
      return CaseStatus.APPROVED
    elif "NEW_CARD" in input:
      return CaseStatus.NEW_CARD
    elif "MAILED" in input:
      return CaseStatus.MAILED
    elif "USPS_PICKED" in input:
      return CaseStatus.USPS_PICKED
    elif "DELIVERED" in input:
      return CaseStatus.DELIVERED
    elif "UNKNOWN" in input:
      return CaseStatus.UNKNOWN
    else:
      return CaseStatus.UNKNOWN

  @classmethod
  def string_to_status(self, input):
    if "Case Was Received" in input:
      return CaseStatus.RECEIVED
    elif "Approved" in input:
      return CaseStatus.APPROVED
    elif "New Card Is Being Produced" in input:
      return CaseStatus.NEW_CARD
    elif "Card Was Mailed To Me" in input:
      return CaseStatus.MAILED
    elif "Card Was Picked Up" in input:
      return CaseStatus.USPS_PICKED
    elif "Card Was Delivered" in input:
      return CaseStatus.DELIVERED
    else:
      return CaseStatus.UNKNOWN
