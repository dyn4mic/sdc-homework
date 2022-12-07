import dashboard
import api
import multiprocessing
jobs = []
jobs.append(multiprocessing.Process(target=api.start))
jobs.append(multiprocessing.Process(target=dashboard.start))

for j in jobs:
    j.start()
