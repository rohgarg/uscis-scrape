from signal import getsignal, signal, SIGINT
from sys import exit
from numpy import array

def log_error(e):
  """
  It is always a good idea to log errors.
  This function just prints them, but you can
  make it do anything.
  """
  print(e)

def construct_app_num(num: int) -> str:
  """
  Returns the application receipt number string for the given application
  number (Integer).
  """
  return 'YSC1990%d' % (num)

def install_sighandler(handler) -> None:
  """
  Sets up the signal handler for SIGINT (^C)
  """
  signal(SIGINT, handler)
