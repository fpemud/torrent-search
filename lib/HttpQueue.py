#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import httplib2
from gi.repository import GObject
import _thread


class HttpQueueClient(object):
    def __init__(self, queue):
        self._queue = queue
        self._client = httplib2.Http()
        self._busy = False
        self._busy_lock = _thread.allocate_lock()          # FIXME
        self._finished = False
        self._finished_lock = _thread.allocate_lock()          # FIXME
        self._request = None
        self._result = None
        self._request_id = None
        self._result_lock = _thread.allocate_lock()          # FIXME

    def _get_busy(self):
        self._busy_lock.acquire()
        res = self._busy
        self._busy_lock.release()
        return res

    def _set_busy(self, value):
        self._busy_lock.acquire()
        self._busy = value
        self._busy_lock.release()
    busy = property(_get_busy, _set_busy)

    def _get_finished(self):
        self._finished_lock.acquire()
        res = self._finished
        self._finished_lock.release()
        return res

    def _set_finished(self, value):
        self._finished_lock.acquire()
        self._finished = value
        self._finished_lock.release()
    finished = property(_get_finished, _set_finished)

    def _get_result(self):
        self._result_lock.acquire()
        res = self._result
        self._result_lock.release()
        return res

    def _set_result(self, value):
        self._result_lock.acquire()
        self._result = value
        self._result_lock.release()
    result = property(_get_result, _set_result)

    def _check_finished(self):
        if self.finished:
            self._queue.send_response(self._request_id, self.result)
            self.busy = False
            return False
        else:
            return True

    def _do_run(self, *request):
        try:
            self.result = self._client.request(*request)
        finally:
            self.finished = True

    def run(self, request_id, *request):
        self.busy = True
        self._request = request
        self._request_id = request_id
        self.result = None
        self.finished = False
        GObject.timeout_add(100, self._check_finished)
        _thread.start_new_thread(self._do_run, request)          # FIXME


class HttpQueue(object):
    def __init__(self, nb_clients=10):
        self._clients = []
        for i in range(nb_clients):
            self._clients.append(HttpQueueClient(self))
        self._queue = []
        self._timer = None
        self._queue_lock = _thread.allocate_lock()          # FIXME
        self._running = False
        self._request_id = 0
        self._request_id_lock = _thread.allocate_lock()          # FIXME
        self._results = {}
        self._results_lock = _thread.allocate_lock()          # FIXME
        self._requests_locks = {}

    def _do_request(self, uri, method='GET', body=None, headers=None, redirections=5, connection_type=None):
        if not self._running:
            return
        self._queue_lock.acquire()
        self._queue.append((uri, method, body, headers,
                            redirections, connection_type))
        self._queue_lock.release()

    def request(self, uri, method='GET', body=None, headers=None, redirections=5, connection_type=None):
        self._request_id_lock.acquire()
        self._request_id += 1
        request_id = self._request_id
        # FIXME
        self._requests_locks[request_id] = _thread.allocate_lock()
        self._request_id_lock.release()
        self._queue_lock.acquire()
        self._queue.append((request_id, uri, method, body,
                            headers, redirections, connection_type))
        self._queue_lock.release()

        self._requests_locks[request_id].acquire()
        self._requests_locks[request_id].acquire()
        self._requests_locks[request_id].release()

        self._results_lock.acquire()
        res = self._results[request_id]
        del self._results[request_id]
        del self._requests_locks[request_id]
        self._results_lock.release()
        return res

    def start(self):
        self._timer = GObject.timeout_add(100, self._check_queue)
        self._running = True

    def stop(self):
        if self._timer:
            GObject.source_remove(self._timer)
        self._timer = None
        self._running = False

    def _check_queue(self):
        self._queue_lock.acquire()
        if len(self._queue) > 0:
            for client in self._clients:
                if (not client.busy) and (len(self._queue) > 0):
                    req = self._queue[0]
                    del self._queue[0]
                    request_id = req[0]
                    req = req[1:]
                    client.run(request_id, *req)
        self._queue_lock.release()
        return True

    def send_response(self, request_id, result):
        self._results_lock.acquire()
        self._results[request_id] = result
        self._requests_locks[request_id].release()
        self._results_lock.release()
