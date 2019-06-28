#!/usr/local/bin/python3

from numpy import array
from time import sleep
from tqdm import tqdm
from argparse import ArgumentParser
from casestatus import CaseStatus
from constants import *
from commonutils import log_error, construct_app_num, install_sighandler
from datautils import save_data, load_data, compare_data, print_stats
from scrapeuscis import get_receipt_status

CKPT_IDX = 0
SAVE_DATA = False

def main() -> None:
  """
  Parses command-line arguments, fetches the USCIS data, and prints the
  aggregate statistics.
  """
  global START, END, RESULTS, WAIT_TIME, CKPT_IDX, SAVE_DATA

  parser = ArgumentParser(description="Get USCIS data")
  parser.add_argument('--start-range', default=DEFAULT_START_RANGE, type=int,
                      help='Starting point of the query (default: {})'
                           .format(DEFAULT_START_RANGE))
  parser.add_argument('--num-elts', default=DEFAULT_NUM_ELTS, type=int,
                      help='Num of receipts to query from starting point (default: {})'
                           .format(DEFAULT_NUM_ELTS))
  parser.add_argument('--save-data', action='store_true',
                      help='Save raw data to CSV (default: false)')
  parser.add_argument('--load-data', metavar='filename.csv', type=str,
                      help='Load raw data from previously saved CSV file')
  parser.add_argument('--compare-data', metavar=('oldfile.csv', 'newfile.csv'),
                      type=str, nargs=2,
                      help='Compare data from previously saved CSV files')
  args = parser.parse_args()
  install_sighandler(exit_gracefully)
  START = args.start_range
  END = args.start_range + args.num_elts
  SAVE_DATA = args.save_data
  if args.load_data:
    (START, END, RESULTS) = load_data(args.load_data)
  elif args.compare_data:
    compare_data(args.compare_data)
    return
  else:
    CKPT_IDX = START
    for i in tqdm(range(START, END)):
      RESULTS.append(get_receipt_status(construct_app_num(i)))
      CKPT_IDX += 1
      sleep(WAIT_TIME)
  print_stats(START, END, SAVE_DATA, array(RESULTS))

def exit_gracefully(signum, frame) -> None:
  """
  Signal handler for SIGINT (^C); prints the statistics so far and kills
  the program.
  """
  global START, END, RESULTS, CKPT_IDX, SAVE_DATA
  if START != None and END != None and len(RESULTS) > 0:
    # This gives us a minimum set of recoverable data
    CKPT_IDX = START + min(len(RESULTS), CKPT_IDX - START)
    print_stats(START, CKPT_IDX, SAVE_DATA, array(RESULTS))
  exit(0)

if __name__ == "__main__":
  main()
