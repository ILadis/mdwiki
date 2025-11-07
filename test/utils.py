
import hashlib
import subprocess
import urllib, re

class MdWikiInstance:
    @classmethod
    def start(cls):
        cls.baseurl = 'http://localhost'
        cls.process = subprocess.Popen(['python', './mkdocs.pyz'], stdout=subprocess.PIPE)

        while True:
            line = cls.process.stdout.readline().decode('utf-8')
            match = re.search(r'Serving on (.+)/$', line)
            if match:
                cls.baseurl = match.group(1)
                break

    @classmethod
    def call_api(cls, method, path, data=''):
        request = urllib.request.Request(f'{cls.baseurl}/{path}', data.encode('utf-8'), method=method)

        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            response = error

        return response

    @classmethod
    def stop(cls):
        cls.process.terminate()
        cls.process.wait()