#!/usr/local/bin/python3

from numpy import array, sum, savetxt, loadtxt, zeros, arange, vectorize
from datetime import datetime
from commonutils import log_error
from casestatus import CaseStatus

def save_data(start: int, end: int, data: array) -> None:
  """
  Save raw data to a CSV file for later use.
  """
  filename = datetime.today().strftime('%Y-%b-%d-%H-%M-%S.csv')
  result = zeros(data.size, dtype=[('appNum', int), ('status', 'U12')])
  result['appNum'] = arange(start, end)
  result['status'] = data
  savetxt(filename, result, header='AppReceiptNum, CaseStatus',
          delimiter=',', fmt='%d, %s')

def load_data(filename: str) -> (int, int, array):
  """
  Reads raw data from the given CSV file and returns the range (start, end) of
  application receipt numbers and the case status array
  """
  to_status = lambda item: CaseStatus.csv_to_status(item)
  result = loadtxt(filename, delimiter=',', skiprows=1,
                   dtype={'names': ('appNum', 'status'),
                          'formats': ('i', 'U12')})
  return (min(result['appNum']), max(result['appNum']),
          vectorize(to_status)(result['status']))

def compare_data(filenames: [str]) -> None:
  """
  Reads raw data from the two given CSV files, compares the data, and
  prints the list of applications that have changed status
  """
  result1 = loadtxt(filenames[0], delimiter=',', skiprows=1,
                    dtype={'names': ('appNum', 'status'),
                           'formats': ('i', 'U12')})
  result2 = loadtxt(filenames[1], delimiter=',', skiprows=1,
                    dtype={'names': ('appNum', 'status'),
                           'formats': ('i', 'U12')})

  if not(are_comparable(result1, result2)):
    log_error("The two files ({} and {}) are not comparable."
              .format(filenames[0], filenames[1]))
    return

  print("{:<8}  {:<17} {}".format("App #", "Old Status", "New Status"))
  print("--------------------------------------")
  for (app, res1, res2) in zip(result1['appNum'], result1['status'], result2['status']):
    if res1 != res2:
      print("{:<7} : {:<13} --> {}".format(app, res1, res2))

def print_stats(start: int, end: int, save: bool, data: array) -> None:
  """
  Prints the aggregate statistics from the data in the given numpy array.
  """
  if save:
    save_data(start, end, data)
  print('***** Stats *****')
  todate = datetime.today().strftime('%Y-%b-%d')
  print('Date: {0}'.format(todate))
  print('Unprocessed: {0}'.format(sum(data == CaseStatus.RECEIVED)))
  print('New Card: {0}'.format(sum(data == CaseStatus.NEW_CARD)))
  print('Approved: {0}'.format(sum(data == CaseStatus.APPROVED)))
  print('Mailed: {0}'.format(sum(data == CaseStatus.MAILED)))
  print('Delivered: {0}'.format(sum(data == CaseStatus.DELIVERED)))
  print('Picked By USPS: {0}'.format(sum(data == CaseStatus.USPS_PICKED)))
  print('Unknown: {0}'.format(sum(data == CaseStatus.UNKNOWN)))

def are_comparable(res1: array, res2: array) -> bool:
  """
  Returns True if two given result arrays are comparable, False otherwise.
  Two arrays are comparable if their minimum and maximum match and they are of
  the same length.
  """
  return min(res1['appNum']) == min(res2['appNum']) and \
         max(res1['appNum']) == max(res2['appNum']) and \
         len(res1['appNum']) == len(res2['appNum'])
