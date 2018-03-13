# -*- coding: utf-8 -*-
import pycurl
import urllib
try:
    from cStringIO import StringIO
except ImportError:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO


class CURLClient(object):
    def __init__(self, url):
        self.c_buffer = StringIO()
        self.url = url
        self.c = pycurl.Curl()
        self.c.setopt(self.c.NOSIGNAL, 1)
        self.c.setopt(self.c.CONNECTTIMEOUT, 30)
        self.c.setopt(self.c.TIMEOUT, 60)

    def request_post(self, header, body):
        if isinstance(body, dict):
            post_body = urllib.urlencode(body)
        elif isinstance(body, str):
            post_body = body
        else:
            post_body = ''

        self.c.setopt(self.c.URL, self.url)
        self.c.setopt(self.c.POST, 1)
        self.c.setopt(self.c.HTTPHEADER, header)
        self.c.setopt(self.c.POSTFIELDS, post_body)
        self.c.setopt(self.c.WRITEDATA, self.c_buffer)

        try:
            self.c.perform()
        except pycurl.error as ex:
            print(ex.message)
        finally:
            self.c.close()

        return self.c_buffer.getvalue()

    def request_get(self):
        self.c.setopt(self.c.URL, self.url)
        try:
            self.c.perform()
        except pycurl.error as ex:
            print(ex.message)
        finally:
            self.c.close()

        return self.c_buffer.getvalue()


if __name__ == '__main__':
    head = ''
    resp_str = ''
    c = CURLClient('http://127.0.0.1:5000')
    response = c.request_post(head, resp_str)
