# RESTful API #
Lucky CAT offers several RESTful endpoints that allow the easy integration and automation of it. This document gives an overview
of the implemented endpoints.

## Testing the RESTful API with requests ##
To quickly start with the API, use [requests](http://docs.python-requests.org). First, you have to acquire an authentication token.
You can check the authentication token of a user in the web interface (user profile).

Afterwards, you can send your requests, e.g. listing the current jobs:
```python
url = "https://localhost:5000/api/jobs"
r = requests.get(url, 
                 headers={'Authorization': token, 
                 'content-type': 'application/json'})
print(r.json())
```
## Jobs ##
There are several endpoints to create, delete and list jobs:
- /api/jobs (GET): lists the currently registered jobs
- /api/job/<job_id> (GET): lists job information for job <job_id>
- /api/job/<job_id> (DELETE): deletes the job with <job_id>
- /api/job (PUT): creates a new job

## TestCase:
- /api/<job_id>/testcase/<testcase_id> (GET): Get TestCase by id
- /api/<job_id>/testcases (GET): lists the currently registered testcases
- /api/<job_id>/testcase/<testcase_id> (PUT): Update TestCase
- /api/<job_id>/testcase/ (PUT): Add TestCase
- Upload Testcase Folder (Store to storage vault)

## Bot: 
- Update Bot Heartbeat
```json
{
  'task_status': "NA",
  'last_beat_time': "now"

}
```

- Register Bot
```json
{
  'bot_name': "bot_name",
  'task_status': "NA",
  'task_payload': "task_payload",
  'task_end_time': "task_end_time",
  'last_beat_time': "last_beat_time",
  'platform': "platform"
}
- ```
## Task
- /api/task (GET): Get Task (by platform)
- /api/task (PUT): Add Task (By platform)
- Send Crash
- Send Stats
- update_task_status

## JobTempale
- Get Template
- Add Template

## Fuzzer
- /api/fuzzers (GET): Get Fuzzers
- /api/fuzzer/<fuzzer_name> (GET): Get Fuzzer
- /api/fuzzer (PUT): Add Fuzzer
- /api/fuzzer/<fuzzer_name> (DELETE): Delete Fuzzer
- Edit Fuzzer

## Bot ##

## Crashes ##
