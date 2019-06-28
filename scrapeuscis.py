from requests import post
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from commonutils import log_error
from casestatus import CaseStatus

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

def raw_to_status(headers) -> CaseStatus:
  """
  Takes in a list of headers from the result HTML and returns an enum
  indicating the case status.

  TODO: Improve parsing and handle more cases
  """
  for header in headers:
    return CaseStatus.string_to_status(header.text)
