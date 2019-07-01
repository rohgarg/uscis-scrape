#!/usr/local/bin/python3

from signal import getsignal, signal, SIGINT
from sys import exit, stderr
from constants import APP_PREFIX

def log_error(msg: str) -> None:
  """
  Logs message to stderr
  """
  print(msg, file=stderr)

def construct_app_num(num: int) -> str:
  """
  Returns the application receipt number string for the given application
  number (Integer).
  """
  return '{}{}'.format(APP_PREFIX, num)

def install_sighandler(handler) -> None:
  """
  Sets up the signal handler for SIGINT (^C)
  """
  signal(SIGINT, handler)
