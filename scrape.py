#!/usr/local/bin/python3

from numpy import array
from time import sleep
from tqdm import tqdm
from argparse import ArgumentParser
from casestatus import CaseStatus
from constants import START, END, RESULTS, WAIT_TIME
from commonutils import log_error, construct_app_num, install_sighandler
from datautils import save_data, load_data, compare_data, print_stats
from scrapeuscis import get_receipt_status

def main() -> None:
  """
  Parses command-line arguments, fetches the USCIS data, and prints the
  aggregate statistics.
  """
  global WAIT_TIME, START, END, RESULTS

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
  install_sighandler(exit_gracefully)
  START = args.start_range
  END = args.start_range + args.num_elts
  if args.load_data:
    (START, END, RESULTS) = load_data(args.load_data)
  elif args.compare_data:
    compare_data(args.compare_data)
    return
  else:
    for i in tqdm(range(START, END)):
      RESULTS.append(get_receipt_status(construct_app_num(i)))
      sleep(WAIT_TIME)
  print_stats(START, END, args.save_data, array(RESULTS))

def exit_gracefully(signum, frame) -> None:
  """
  Signal handler for SIGINT (^C); prints the statistics so far and kills
  the program.

  TODO: Check if user had asked us to save data, and then save the partial
  data to a CSV file.
  """
  if START != None and END != None and len(RESULTS) > 0:
    print_stats(START, END, False, array(RESULTS))
  exit(0)

if __name__ == "__main__":
  main()
