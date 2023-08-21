import logging
import re
import requests
import json


class TPCRest:
    def __init__(self, ip, port=5000):
        self.ip = ip
        self.port = port
        self.status = ''

    @property
    def endpoint(self):
        return f"http://{self.ip}:{self.port}"

    def send_request(self, endpoint, method="GET", json=True):
        url = f"{self.endpoint}/{endpoint}"
        data = False
        try:
            if method == "GET":
                response = requests.get(url, timeout=3)
            elif method == "POST":
                response = requests.post(url, timeout=3)
            response.raise_for_status()
            if json:
                logging.debug(f"Sending request to {url}")
                data = response.json()
            else:
                data = response.content
        except requests.exceptions.HTTPError as h:
            self.status = self.format_status(h)
        except requests.exceptions.ConnectionError as c:
            self.status = self.format_status(c)
        except requests.exceptions.Timeout as t:
            self.status = self.format_status(t)
        except requests.exceptions.JSONDecodeError as j:
            self.status = self.format_status(j)
        except requests.exceptions.RequestException as r:
            self.status = self.format_status(r)
        except Exception as e:
            self.status = self.format_status(e)
        if data:
            self.status = ''
        else:
            logging.error(self.status.replace('\n', '>>'))
        return data

    def post_request(self, endpoint, js):
        logging.info(f"Send request: {js}")
        url = f"{self.endpoint}/{endpoint}"
        data = False
        try:
            response = requests.post(url, timeout=3, json=js)
            logging.info(f"Response data: {response.json()}")
            response.raise_for_status()
            logging.debug(f"Sending request to {url}")
            data = response.json()
        except requests.exceptions.HTTPError as h:
            self.status = self.format_status(h)
        except requests.exceptions.ConnectionError as c:
            self.status = self.format_status(c)
        except requests.exceptions.Timeout as t:
            self.status = self.format_status(t)
        except requests.exceptions.JSONDecodeError as j:
            self.status = self.format_status(j)
        except requests.exceptions.RequestException as r:
            self.status = self.format_status(r)
        except Exception as e:
            self.status = self.format_status(e)
        if data:
            self.status = ''
        else:
            logging.error(self.status.replace('\n', '>>'))
        return data

    @staticmethod
    def format_status(status):
        try:
            rep = {"HTTPConnectionPool": "", "/server/info ": "", "Caused by ": "", "(": "", ")": "",
                   ": ": "\n", "'": "", "`": "", "\"": ""}
            rep = {re.escape(k): v for k, v in rep.items()}
            pattern = re.compile("|".join(rep.keys()))
            status = pattern.sub(lambda m: rep[re.escape(m.group(0))], f"{status}").split("\n")
            return "\n".join(_ for _ in status if "urllib3" not in _ and _ != "")
        except TypeError or KeyError:
            return status
