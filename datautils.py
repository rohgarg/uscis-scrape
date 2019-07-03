#!/usr/local/bin/python3

from numpy import array, sum, savetxt, loadtxt, zeros, arange, vectorize
from datetime import datetime
from commonutils import construct_app_num, log_error
from casestatus import CaseStatus
from typing import Tuple, List
from functools import reduce
from os.path import basename
from itertools import tee

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

def load_data(filename: str) -> Tuple[int, int, array]:
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

def compare_data(filenames: List[str]) -> None:
  """
  Reads raw data from the given CSV files (at least 2), compares the data, and
  prints the list of applications that have changed status
  """
  if len(filenames) < 2:
    log_error("Specify at least 2 files for comparison.")
    return

  results = []
  for f in filenames:
    results.append(loadtxt(f, delimiter=',', skiprows=1,
                           dtype={'names': ('appNum', 'status'),
                                  'formats': ('i', 'U12')}))
  for (x, y) in pairwise(results):
    if not(are_comparable(x, y)):
      log_error('The files are not comparable.')
      return

  header = '{:<11}'.format('App #')
  prepHead = lambda x, y: '{:<16} {:<17}'.format(extract_date_from_filename(x),
                                                 extract_date_from_filename(y))
  print(reduce(prepHead, filenames, header))
  print('-----------' + '------------------' * len(filenames))

  for (i, app) in enumerate(results[0]['appNum']):
    line = '{:9} : {:<13}'.format(construct_app_num(app), results[0][i]['status'])
    shouldPrint = False
    for (x, y) in pairwise(results):
      if x[i]['status'] != y[i]['status']:
        line += ' --> {:<13}'.format(y[i]['status'])
        shouldPrint = True
      else:
        break
    if shouldPrint:
      print(line)

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

def extract_date_from_filename(filename: str) -> str:
  parts = basename(filename).split('-')
  if len(parts) <= 2:
    return filename
  return '{} {}, {}'.format(parts[1], parts[2], parts[0])

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)
