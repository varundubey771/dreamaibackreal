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

@dataclass
class SymbolLink:
    symbol:str
    link:str
    title:str

@dataclass
class SymbolInterpretation:
    symbol:str
    interpretation:str

@dataclass
class Job:
    jobId:str
    events:List[Event]
    symbols:List[str]
    symbolLinks:List[SymbolLink]
    status:str
    result:str
    symbolInterpretations:List[SymbolInterpretation]
    costing:List[any]

class SingletonJobsKv:
    _instance_ = None
    def __init__(self):
        if not SingletonJobsKv._instance_:
            self.store:Dict[str:Job] = {}
            self.lock = Lock()
            SingletonJobsKv._instance_ = self
        else:
            print("???")

    @classmethod
    def getInstance(cls):
        if not cls._instance_:
            cls()
        return cls._instance_

    def getJob(self, jobId):
        if jobId in self.store:
            return self.store[jobId]
        return {"status":"jobNotFound"}

    def getJobForApi(self, jobId):
        if jobId in self.store:
            return {"symbols":self.store[jobId].symbols[:], "symbolLinks":self.store[jobId].symbolLinks[:], "status":self.store[jobId].status, "symbolInterpretations":self.store[jobId].symbolInterpretations[:]}
        return {"status":"jobNotFound"}

    def getLock(self):
        return self.lock

    def updateJobSymbols(self, jobId:str, symbols:List[str]):
        try:
            if jobId in self.store:
                self.store[jobId].symbols.extend(symbols)
                return {"status":"updateJobSymbolsSuccess"}
        except Exception as e:
            print(str(e))
            return {"status":"updateJobSymbolsError"}
        return {"status":"jobNotFound"}

    def updateJobSymbolLinks(self, jobId:str, symbolLinks:List[SymbolLink]):
        try:
            if jobId in self.store:
                self.store[jobId].symbolLinks.extend(symbolLinks)
                return {"status":"updateJobSymbolLinksSuccess"}
        except Exception as e:
            print(str(e))
            return {"status":"updateJobSymbolLinksError"}
        return {"status":"jobNotFound"}

    def updateJobResult(self, jobId:str, result:str):
        try:
            if jobId in self.store:
                self.store[jobId].result=result
                return {"status":"updateJobResultSuccess"}
        except Exception as e:
            print(str(e))
            return {"status":"updateJobResultError"}
        return {"status":"jobNotFound"}

    def updateJobStatus(self, jobId:str, status:str):
        try:
            if jobId in self.store:
                self.store[jobId].status = status
                return {"status":"updateJobStatusSuccess"}
        except Exception as e:
            print(str(e))
            return {"status":"updateJobStatusError"}
        return {"status":"jobNotFound"}

    def appendEvent(self, jobId:str, eventData:str):
        try:
            if not jobId in self.store:
                print("job staryed", jobId)
                self.store[jobId] = Job(jobId=jobId, status="RUNNING", events = [], symbols=[], symbolLinks=[], result="", symbolInterpretations=[], costing=[])
            else:
                self.store[jobId].events.append(Event(timestamp=datetime.now(), data=eventData))
            return {"status":"appendEventSuccess"}
        except Exception as e:
            print(str(e))
            return {"status":"appendEventError"}

    def appendSymbolLink(self, jobId:str, symbolLink:SymbolLink):
        try:
            if jobId in self.store:
                self.store[jobId].symbolLinks.append(symbolLink)
                res = "appendSymbolLinkSuccess"+str(symbolLink.symbol)
                return {"status":res}
            return {"status":"jobNotFound"}
        except Exception as e:
            print(str(e))
            return {"status":"appendSymbolLinkError"}

    def appendSymbolInterpretation(self, jobId:str, symbolInterpretation:SymbolInterpretation):
        try:
            if jobId in self.store:
                self.store[jobId].symbolInterpretations.append(symbolInterpretation)
                res = "appendSymbolInterpretationSuccess"+str(symbolInterpretation.symbol)
                return {"status":res}
            return {"status":"jobNotFound"}
        except Exception as e:
            print(str(e))
            return {"status":"appendSymbolInterpretationError"}
    def appendCosting(self, jobId:str, costObj):
        if jobId in self.store:
            self.store[jobId].costing.append(costObj)
            return {"status":"appendCostingSuccess"}
        return {"status":"jobNotFound"}
    def flushEvents(self):
        pass



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