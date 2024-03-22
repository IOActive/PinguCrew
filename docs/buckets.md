# Blobs_BUCKET
Default bucket to store blobs, e.g. testcases, fuzzer archives, etc.

# RELEASE_BUILD_BUCKET_PATH
Indicates a path to the build that is uploaded to Storage bucket. See [specifying a continuous build] for more detail.

# DEPLOYMENT_BUCKET
Bucket to store deployment artifacts, e.g. source archives, etc.

# CORPUS_BUCKET
Default bucket to store corpus / useful testcases found during fuzzing. This has sub-directories
for each fuzzer, but not for jobs. So, unless you override this in a job definition, a fuzzer
across different jobs share the same corpus (e.g. useful for different fuzzing engines to
cross-pollinate the corpus)

# BACKUP_BUCKET
Default bucket to store minimized corpus for various fuzzers. Once a day, corpus pruning task
minimizes the current corpus in CORPUS_BUCKET and then archives it in this bucket. You can
customize it to be different from the backup bucket above if you want separation from other
backup items like datastore backups, etc.

# QUARANTINE_BUCKET
Default bucket to store quarantined corpus items. These items prevent fuzzer from making
progress during fuzzing (e.g. crashes, timeout, etc), so we automatically quarantine them once
they sneak into the corpus somehow. Once the bugs are fixed, items from quarantine are brought
back into the main corpus bucket.

# SHARED_CORPUS_BUCKET: test-shared-corpus-bucket
Default bucket to store shared corpus across all job types. This is planned for future cross
pollination with other data sources on the web.

#  FUZZ_LOGS_BUCKET
Default bucket to store fuzzing logs from testcase runs. This is different from the fuzzer logs
above which logs the fuzzer run that generates the testcases, whereas this one logs the run of
the testcases against the target application.

# MUTATOR_PLUGINS_BUCKET
Default bucket to store mutator plugins.

# BIGQUERY_BUCKET
Bucket to store bigquery artifacts, e.g. crash stats, etc.

# COVERAGE_BUCKET
Bucket to load code coverage information from.
