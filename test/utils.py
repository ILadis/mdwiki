
import logging
import urllib, re
import urllib.request

class MdWikiInstance:
    @classmethod
    def start(cls):
        import threading
        from mdwiki.utils import capture_logging
        from mkdocs.commands import serve

        logs = capture_logging()
        thread = threading.Thread(target=serve.serve)
        thread.start()

        while True:
            try:
                record = logs.get_nowait()
            except:
                thread.join(timeout=0.1)
                continue

            match = re.search(r'Serving on (.+)/$', record.message)
            if match:
                cls.baseurl = match.group(1)
                cls.thread = thread
                break

    @classmethod
    def call_api(cls, method, path, data='', headers={}, defer=None):
        # TODO accomplish this differently
        headers['Authorization'] = 'Bearer 123'
        request = urllib.request.Request(f'{cls.baseurl}/{path}', data.encode('utf-8'), method=method, headers=headers)

        def execute():
            try:
                response = urllib.request.urlopen(request)
            except urllib.error.HTTPError as error:
                response = error
            return response

        return execute() if not defer else defer.run_in_executor(None, execute)

    @classmethod
    def stop(cls):
        cls.thread.stop()
        cls.thread.join()
