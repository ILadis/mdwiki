
import queue
import signal
import threading
import logging, io
import logging.handlers
import types

def capture_logging():
    logs = queue.Queue()
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding='utf-8', write_through=True)

    handler1 = logging.StreamHandler()
    handler1.name = 'MkDocsStreamHandler'
    handler1.setStream(stream)

    # prevents changing stream to actual sysout
    noop = lambda self, stream: None
    handler1.setStream = types.MethodType(noop, handler1)

    # logs are captured using a queue
    handler2 = logging.handlers.QueueHandler(logs)
    handler2.name = 'MkDocsQueueHandler'

    logger = logging.getLogger('mkdocs')
    logger.addHandler(handler1)
    logger.addHandler(handler2)

    return logs

def setup_logging(stream, level, pattern):
    levels = {
        'debug': logging.DEBUG,
        'info':  logging.INFO,
        'warn':  logging.WARNING,
        'error': logging.ERROR
    }

    # stips timestamps from live reload server logs
    def format_message(self, record):
        if record.name == 'mkdocs.livereload':
            record.name = 'mkdocs.server'
            record.message = record.msg[11:]
        return self._style.format(record)

    formatter = logging.Formatter(pattern)
    formatter.formatMessage = types.MethodType(format_message, formatter)

    logger = logging.getLogger('mkdocs')
    logger.setLevel(levels[level])

    handler = logging.getHandlerByName('MkDocsStreamHandler')

    if handler is None:
        handler = logging.StreamHandler()
        handler.name = 'MkDocsStreamHandler'
        logger.addHandler(handler)

    handler.setStream(stream)
    handler.setFormatter(formatter)

def disable_livereload_jsinject(server):
    noop_inject = lambda self, content, epoch: content
    server._inject_js_into_html = types.MethodType(noop_inject, server)

def enable_graceful_shutdown(server):
    thread = threading.current_thread()
    handler = lambda *args: server.shutdown(wait=True)

    if thread is threading.main_thread():
        signal.signal(signal.SIGTERM, handler)
    else:
        thread.stop = handler
