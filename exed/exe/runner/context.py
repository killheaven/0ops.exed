# -*- coding: utf-8 -*-

import multiprocessing

import redis
import celery

from exe.cfg import CONF
from exe.cfg import ModuleOpts
from exe.exc import ConfigError
from exe.executor import AnsibleExecutor as Executor


## Consts ##
DEFAULT_CONCURRENCY = multiprocessing.cpu_count()
DEFAULT_CONF = {
    'redis_url'     : "redis://localhost",
    'broker_url'    : "amqp://guest:guest@localhost:5672//",
    'executor'      : "ansible",
    'concurrency'   : DEFAULT_CONCURRENCY,
}


class Context(celery.Task):

    __RUNNER_NAME__ = None
    __RUNNER_MUTEX_REQUIRED__ = False

    def __init__(self):
        """ Init Context for each Runner, which provide some config infomations.
        
            At celery worker point of view,
                The `Context` will be created by celery worker before
                execute `CeleryWorkerInit`, which means the `cfgread` has not
                run, so that `CONF` struct will be empty here. """
        self._cfg = None
        self._rpool = None
        self._concurrency = None
        self._executor_opts = None

    @property
    def cfg(self):
        if self._cfg == None:
            try:
                self._cfg = CONF.runner
            except ConfigError:
                self._cfg = ModuleOpts("", DEFAULT_CONF)
            self._cfg.merge(DEFAULT_CONF)
        return self._cfg

    @property
    def concurrency(self):
        if self._concurrency == None:
            _concurrency = self._cfg.concurrency
            if not _concurrency:
                _concurrency = DEFAULT_CONCURRENCY
            self._concurrency = _concurrency
        return self._concurrency

    @property
    def runner_name(self):
        return self.__RUNNER_NAME__

    @property
    def runner_mutex(self):
        return self.__RUNNER_MUTEX_REQUIRED__

    @property
    def redis(self):
        if not self._rpool:
            self._rpool = redis.ConnectionPool.from_url(url=self.cfg.redis_url)
        return redis.Redis(connection_pool=self._rpool)

    def executor(self, targets=[]):
        if not self._executor_opts:
            self._executor_opts = CONF.module(self.cfg.executor)
        return Executor(targets, **self._executor_opts.dict_opts)
