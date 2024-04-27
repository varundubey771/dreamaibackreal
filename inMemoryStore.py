from datetime import datetime
from dataclasses import dataclass
from threading import Lock
from typing import List, Dict

@dataclass
class Event:
    timestamp:datetime
    data:str

@dataclass
class Job:
    status:str
    events: List[Event]
    analysisSummary:str
    rawAnalysis:str

class SingletonInMemoryEvents:
    _instance_=None
    def __init__(self):
        if not SingletonInMemoryEvents._instance_:
            self.jobsLock = Lock()
            self.jobs: Dict[str, Job] = {}
            SingletonInMemoryEvents._instance_=self
        else:
            print("pls call getSingleInstance")

    @classmethod
    def getSingleInstance(cls):
        if cls._instance_==None:
            cls()
        return cls._instance_

    def appendEvent(self, jobId:str, eventData:str):
        with self.jobsLock:
            print("@@@@@@@@@@@@@@grabbedlocks")
            if not jobId in self.jobs:
                print("job staryed", jobId)
                self.jobs[jobId] = Job(status = "started", events = [], analysisSummary="", rawAnalysis="")
            else:
                print("append event for jobv")
                self.jobs[jobId].events.append(Event(timestamp=datetime.now(), data=eventData))

    def updateJobRawAnalysis(self,jobId:str, res:str):
        with self.jobsLock:
            if not jobId in self.jobs:
                pass
            else:
                self.jobs[jobId].rawAnalysis=res

    def updateJobAnalysisSummary(self,jobId:str, res:str):
        with self.jobsLock:
            if not jobId in self.jobs:
                pass
            else:
                self.jobs[jobId].analysisSummary=res

    def updateJobStatus(self,jobId:str, status:str):
        with self.jobsLock:
            if not jobId in self.jobs:
                pass
            else:
                self.jobs[jobId].status=status

    def updateRawAnalysis(self, jobId:str, rawAnalysis):
        with self.jobsLock:
            if not jobId in self.jobs:
                pass
            else:
                self.jobs[jobId].rawAnalysis=rawAnalysis

    def getJob(self, jobId:str):
        # with self.jobsLock:
        #     if not jobId in self.jobs:
        #         return
        #     else:
        return self.jobs.get(jobId)
    def getLock(self):
        return self.jobsLock


# class SingletonEvents:
#     def __init__(self):
#         self.jobsLock = Lock()
#         self.jobs: Dict[str, Job] = {}
#     def appendEvent(jobId:str, eventData:str, status:str='', ):
#         with self.jobsLock:
#             print("@@@@@@@@@@@@@@grabbedlocks")
#             if not jobId in jobs:
#                 print("job staryed", jobId)
#                 self.jobs[jobId] = Job(status = "started", events = [], res = "")
#             else:
#                 print("append event for jobv")
#                 jobs[jobId].events.append(Event(timestamp=datetime.now(), data=eventData))