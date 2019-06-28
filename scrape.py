#!/usr/local/bin/python3

from requests import post
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from enum import Enum
from numpy import array, sum, savetxt, loadtxt, zeros, arange, vectorize
from time import sleep
from tqdm import tqdm
from argparse import ArgumentParser
from datetime import datetime
from signal import getsignal, signal, SIGINT
from sys import exit

ORIGINAL_SIGINT = None
START = None
END = None
RESULTS = []
WAIT_TIME = 0.1

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

def simple_post(url: str, params: set, header: set):
  """
  Attempts to get the content at `url` by making an HTTP POST request.
  If the content-type of response is some kind of HTML/XML, return the
  text content, otherwise return None.
  """
  try:
    resp = post(url, data=params, headers=header)
    with closing(resp):
      if is_good_response(resp):
        return resp.content
      else:
        return None
  except RequestException as e:
    log_error('Error during requests to {0} : {1}'.format(url, str(e)))
    return None

def is_good_response(resp) -> bool:
  """
  Returns True if the response seems to be HTML, False otherwise.
  """
  content_type = resp.headers['Content-Type'].lower()
  return (resp.status_code == 200
          and content_type is not None
          and content_type.find('html') > -1)

def log_error(e):
  """
  It is always a good idea to log errors.
  This function just prints them, but you can
  make it do anything.
  """
  print(e)

def raw_to_status(headers) -> CaseStatus:
  """
  Takes in a list of headers from the result HTML and returns an enum
  indicating the case status.

  TODO: Improve parsing and handle more cases
  """
  for header in headers:
    return CaseStatus.string_to_status(header.text)

def get_receipt_status(receipt_num: str) -> CaseStatus:
  """
  Returns the case status for the given receipt number.
  """
  req_header = {'Host': 'egov.uscis.gov',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:67.0) Gecko/20100101 Firefox/67.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://egov.uscis.gov/casestatus/landing.do',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': '69',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1'}
  req_params = {'changeLocale': '',
                'appReceiptNum': receipt_num,
                'initCaseSearch': 'CHECK+STATUS'}
  url = 'https://egov.uscis.gov/casestatus/mycasestatus.do'
  raw_html = simple_post(url, req_params, req_header)
  doc = BeautifulSoup(raw_html, 'html.parser')
  return raw_to_status(doc.find_all('h1'))

def construct_num(num: int) -> str:
  """
  Returns the application receipt number string for the given application
  number (Integer).
  """
  return 'YSC1990%d' % (num)

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

def are_comparable(res1: array, res2: array) -> bool:
  """
  Returns True if two given result arrays are comparable, False otherwise.
  Two arrays are comparable if their minimum and maximum match and they are of
  the same length.
  """
  return min(res1['appNum']) == min(res2['appNum']) and \
         max(res1['appNum']) == max(res2['appNum']) and \
         len(res1['appNum']) == len(res2['appNum'])

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

def exit_gracefully(signum, frame) -> None:
  """
  Signal handler for SIGINT (^C); prints the statistics so far and kills
  the program.
  """
  global ORIGINAL_SIGINT, START, END, RESULTS
  signal(SIGINT, ORIGINAL_SIGINT)
  if START != None and END != None and len(RESULTS) > 0:
    print_stats(START, END, False, array(RESULTS))
  exit(0)

def install_sighandler() -> None:
  """
  Sets up the signal handler for SIGINT (^C)
  """
  global ORIGINAL_SIGINT
  ORIGINAL_SIGINT = getsignal(SIGINT)
  signal(SIGINT, exit_gracefully)

def main() -> None:
  """
  Parses command-line arguments, fetches the USCIS data, and prints the
  aggregate statistics.
  """
  global WAIT_TIME, ORIGINAL_SIGINT, START, END, RESULTS

  parser = ArgumentParser(description="Get USCIS data")
  parser.add_argument('--start-range', default=197000, type=int,
                      help='Starting point of the query (default: 197000)')
  parser.add_argument('--num-elts', default=1000, type=int,
                      help='Num of receipts to query from starting point (default: 1000)')
  parser.add_argument('--save-data', action='store_true',
                      help='Save raw data to CSV (default: false)')
  parser.add_argument('--load-data', metavar='filename.csv', type=str,
                      help='Load raw data from previously saved CSV file')
  parser.add_argument('--compare-data', type=str, nargs=2,
                      help='Compare data from previously saved CSV files')
  args = parser.parse_args()
  install_sighandler()
  START = args.start_range
  END = args.start_range + args.num_elts
  if args.load_data:
    (START, END, RESULTS) = load_data(args.load_data)
  elif args.compare_data:
    compare_data(args.compare_data)
    return
  else:
    for i in tqdm(range(START, END)):
      RESULTS.append(get_receipt_status(construct_num(i)))
      sleep(WAIT_TIME)
  print_stats(START, END, args.save_data, array(RESULTS))

if __name__ == "__main__":
  main()
