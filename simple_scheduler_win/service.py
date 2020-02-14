
'''
SMWinservice
by Davide Mastromatteo

Base class to create winservice in Python
-----------------------------------------

Instructions:

1. Just create a new class that inherits from this base class
2. Define into the new class the variables
   _svc_name_ = "nameOfWinservice"
   _svc_display_name_ = "name of the Winservice that will be displayed in scm"
   _svc_description_ = "description of the Winservice that will be displayed in scm"
3. Override the three main methods:
    def start(self) : if you need to do something at the service initialization.
                      A good idea is to put here the inizialization of the running condition
    def stop(self)  : if you need to do something just before the service is stopped.
                      A good idea is to put here the invalidation of the running condition
    def main(self)  : your actual run loop. Just create a loop based on your running condition
4. Define the entry point of your module calling the method "parse_command_line" of the new class
5. Enjoy

https://www.thepythoncorner.com/2018/08/how-to-create-a-windows-service-in-python/
'''


import asyncio
import logging
import os
import sys
import threading

import tornado
from tornado.platform.asyncio import AnyThreadEventLoopPolicy

import servicemanager
import win32event
import win32service
import win32serviceutil

from ndscheduler import settings
from ndscheduler.corescheduler import scheduler_manager
from ndscheduler.server  import server


os.environ["NDSCHEDULER_SETTINGS_MODULE"] = "archive_scheduler.settings"

logger = logging.getLogger(__name__)
logger.info(os.environ["NDSCHEDULER_SETTINGS_MODULE"])


class WinSchedulerServer(server.SchedulerServer):

    def __init__(self, scheduler_instance):
        super().__init__(scheduler_instance)

        self.io_loop = None

    @classmethod
    def run(cls):

        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
        if not cls.singleton:

            sched_manager = scheduler_manager.SchedulerManager(
                scheduler_class_path=settings.SCHEDULER_CLASS,
                datastore_class_path=settings.DATABASE_CLASS,
                db_config=settings.DATABASE_CONFIG_DICT,
                db_tablenames=settings.DATABASE_TABLENAMES,
                job_coalesce=settings.JOB_COALESCE,
                job_misfire_grace_sec=settings.JOB_MISFIRE_GRACE_SEC,
                job_max_instances=settings.JOB_MAX_INSTANCES,
                thread_pool_size=settings.THREAD_POOL_SIZE,
                timezone=settings.TIMEZONE
            )

            cls.singleton = cls(sched_manager)
            cls.singleton.start_scheduler()
            server = cls.singleton.application.listen(settings.HTTP_PORT, settings.HTTP_ADDRESS)
            cls.singleton.server = server
            logger.info('Running server at %s:%d ...' % (settings.HTTP_ADDRESS, settings.HTTP_PORT))
            logger.info('*** You can access scheduler web ui at http://localhost:%d'
                        ' ***' % settings.HTTP_PORT)

            io_loop = tornado.ioloop.IOLoop().current()
            cls.singleton.io_loop = io_loop
            io_loop.start()
            cls.singleton.server.stop()


    @classmethod
    def stop(cls):
        if cls.singleton:
            cls.singleton.stop_scheduler()
            io_loop = cls.singleton.io_loop
            io_loop.add_callback(io_loop.stop)






class SchedulerService(win32serviceutil.ServiceFramework):
    '''Base class to create winservice in Python'''


    _svc_name_ = 'NDSchedulerService'
    _svc_display_name_ = 'NDScheduler'
    _svc_description_ = 'A service that runs the NDScheduler.'


    def __init__(self, args):
        '''
        Constructor of the winservice
        '''
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

        self.loop_interval = 5.0 # loop interval in seconds

        self.thread = threading.Thread(target=WinSchedulerServer.run, name="ServerThread", daemon=True)


    def SvcStop(self):
        '''
        Called when the service is asked to stop
        '''
        # pylint: disable=invalid-name

        self.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)


    def SvcDoRun(self):
        '''
        Called when the service is asked to start
        '''
        # pylint: disable=invalid-name

        self.start()
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def _wait_for_stop(self):

        rc = None

        while rc != win32event.WAIT_OBJECT_0:
            rc = win32event.WaitForSingleObject(self.hWaitStop,
                                                self.loop_interval * 1000)

    def start(self):
        '''
        Override to add logic before the start
        eg. running condition
        '''
        logger.debug("Start Service")
        self.thread.start()


    def stop(self):
        '''
        Override to add logic before the stop
        eg. invalidating running condition
        '''
        logger.debug("Stop Service")
        WinSchedulerServer.stop()
        self.thread.join()


    def main(self):
        '''
        Main class to be ovverridden to add logic
        '''
        logger.debug("Service Main")
        self._wait_for_stop()




# entry point of the module: copy and paste into the new module
# ensuring you are calling the "parse_command_line" of the new created class
if __name__ == '__main__':

    win32serviceutil.HandleCommandLine(SchedulerService)
