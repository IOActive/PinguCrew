**Black-Box Fuzzers (Opaque Fuzzers) Documentation**

**Overview**

**The "Opaque Fuzzers" implementation is a type of black-box fuzzer designed to integrate seamlessly with our fuzzing system, as part of the **do_blackbox_fuzzing** workflow in **fuzz_task.py**. Unlike engine-based fuzzers (e.g., libFuzzer), opaque fuzzers operate without instrumentation or feedback, blindly executing a fuzzer binary and collecting post-execution evidence (crashes, logs, stats, metadata) from designated output directories. This documentation explains how to use and instrument these fuzzers within our system.**

**Key Features**

* **Single-Stage Execution**: Runs the fuzzer without a separate testcase generation and execution phase, relying on the fuzzer’s own logic.
* **Split Output**: Separates crash testcases (**crash-*** files) into a dedicated directory (**crash_testcase_dir**) and other artifacts (logs, stats, metadata) into an **artifacts_dir**.
* **Metadata Support**: Collects issue tracking metadata (e.g., owners, labels) from artifact files.
* **Compatibility**: Integrates with the existing **run** function in **fuzz_task.py**, returning **(fuzzer_metadata, testcase_file_paths, testcases_metadata, crashes)**.

**Prerequisites**

* **Fuzzer Binary/Script**: A standalone fuzzer (e.g., **fuzz.py**) that accepts command-line arguments for input and output directories.

---

**Usage**

**Running an Opaque Fuzzer**

**Opaque fuzzers are executed via the **do_blackbox_fuzzing** method within a **FuzzTask** instance, typically invoked by the **run** method in **fuzz_task.py**. The fuzzer is launched through a shell script (**launcher.sh**) that sets up the environment and calls the fuzzer binary.**

1. **Prepare the Fuzzer**:
   * **Ensure your fuzzer is a script or binary (e.g., **fuzz.py**) located in a directory (e.g., **./examples/htmlparser/**).**
2. **Configure Environment**:
   * **Set environment variables via **bot configuration file or the portal**:**
     * **FUZZER_TIMEOUT**: Duration per fuzzing round (e.g., **3600** seconds).
     * **MAX_TESTCASES**: Number of fuzzing rounds (e.g., **1** for a single run).
     * **FUZZ_INPUTS**: Directory for crash testcases (e.g., **/tmp/fuzz_inputs**).
     * **APP_REVISION**: Build revision (e.g., **"12345"**).
3. **Invoke the Fuzzer**:
   * **The **run** method in **fuzz_task.py** calls **do_blackbox_fuzzing** if the fuzzer is not engine-based:**
     **python**

     ```python
     metadata, testcases, testcases_meta, crashes = do_blackbox_fuzzing(self, fuzzer, fuzzer_directory, job_id)
     ```
   * **Outputs are processed by **run** (e.g., crash uploading, stats tracking).**

**Command-Line Arguments**

**The fuzzer binary (via **launcher.sh**) is invoked with:**

* **--input_dir `<path>`**: Directory containing the input corpus.
* **--crash_testcase_dir `<path>`**: Directory for crash testcases (e.g., **crash-*** files).
* **--artifacts_dir `<path>`**: Directory for logs, stats, and metadata.

**Example:**

**bash**

```bash
./launcher.sh --input_dir /tmp/corpus --crash_testcase_dir /tmp/crashes --artifacts_dir /tmp/artifacts/test_fuzzer
```

---

**Instrumentation**

**Fuzzer Binary/Script Requirements**

**To work with **do_blackbox_fuzzing**, your fuzzer (e.g., **fuzz.py**) must:**

1. **Accept Command-Line Arguments**:
   * **Parse **--input_dir**, **--crash_testcase_dir**, and **--artifacts_dir** using **argparse** or similar.**
   * **Example **fuzz.py**:**
     **python**

     ```python
     import argparse
     import os

     deffuzz(input_dir, crash_testcase_dir, artifacts_dir):
         os.makedirs(crash_testcase_dir, exist_ok=True)
         os.makedirs(artifacts_dir, exist_ok=True)
     # Fuzzing logic: write crash files to crash_testcase_dir.
     withopen(os.path.join(crash_testcase_dir,"crash-12345"),"w")as f:
             f.write("Crash input")
     # Write logs to artifacts_dir.
     withopen(os.path.join(artifacts_dir,"run_log.log"),"w")as f:
             f.write("Crash detected: Segmentation fault\n")

     if __name__ =="__main__":
         parser = argparse.ArgumentParser(description="Black-Box Fuzzer")
         parser.add_argument("--input_dir", required=True,help="Input corpus directory")
         parser.add_argument("--crash_testcase_dir", required=True,help="Crash testcase output directory")
         parser.add_argument("--artifacts_dir", required=True,help="Artifacts output directory")
         args = parser.parse_args()
         fuzz(args.input_dir, args.crash_testcase_dir, args.artifacts_dir)
     ```
2. **Produce Artifacts**:
   * **Crash Testcases**: Write files named **crash-*** (e.g., **crash-12345**) to **--crash_testcase_dir** when a crash occurs.
   * **Logs**: Write **.log** files (e.g., **run_log.log**) to **--artifacts_dir** with crash indicators (e.g., "Segmentation fault", "exception").
   * **Stats**: Optionally write **stats-*.stats** files in JSON format to **--artifacts_dir**:
     **json**

     ```json
     {
     "executions":2000,
     "new_units":50,
     "crashes_found":1,
     "runtime_seconds":60.0,
     "coverage_percent":75.5
     }
     ```
   * **Metadata**: Optionally write files like **.owners**, **.labels**, **.components**, and **.issue_metadata** (JSON) to **--artifacts_dir** for issue tracking.
3. **Exit Codes**:
   * **Return **0** for success, non-zero (e.g., **1**) for crashes or errors, aiding crash detection via **CrashResult**.**

**Launcher Script**

**The launcher (**launcher.sh**) bridges the system’s invocation and **fuzz.py**:**

**bash**

```bash
#!/bin/bash

input_dir=""
crash_testcase_dir=""
artifacts_dir=""

while[["$#" -gt 0]];do
case$1in
        --input_dir)input_dir="$2";shift;;
        --crash_testcase_dir)crash_testcase_dir="$2";shift;;
        --artifacts_dir)artifacts_dir="$2";shift;;
        *)echo"Unknown parameter: $1";exit1;;
esac
shift
done

if[[ -z "$input_dir"|| -z "$crash_testcase_dir"|| -z "$artifacts_dir"]];then
echo"Error: Missing required arguments"
echo"Usage: $0 --input_dir <input_directory> --crash_testcase_dir <crash_output_directory> --artifacts_dir <artifacts_directory>"
exit1
fi

source .venv/bin/activate
python ./examples/htmlparser/fuzz.py "$input_dir" --crash_testcase_dir "$crash_testcase_dir" --artifacts_dir "$artifacts_dir"
```

* **Placement**: Store in the fuzzer directory (e.g., **./examples/htmlparser/launcher.sh**).
* **Executable**: Ensure **chmod +x launcher.sh**.

**System Configuration**

* **Fuzzer Registration**:
  * **Register the fuzzer in the dashboard with **executable_path="launcher.sh"**.**
* **Directory Setup**:
  * **testcase_directory**: Set via **environment.get_value('FUZZ_INPUTS')**.
  * **artifacts_directory**: Set via **environment.get_value('ARTIFACTS_DIR')**.

---

**Artifact Handling**

**Expected Outputs**

* **crash_testcase_dir**:
  * **Files: **crash-*** (e.g., **crash-12345**).**
  * **Purpose: Stores testcases causing crashes, collected by **run_opaque_fuzzer** and verified via **CrashResult**.**
* **artifacts_dir**:
  * **Logs**: **.log** files (e.g., **run_log.log**) with execution details and crash indicators.
  * **Stats**: **stats-*.stats** files in JSON, used for **testcase_run** stats.
  * Coverage: coverage files (eg. .cov).
  * **Metadata**:
    * **.owners**: List of notification emails.
    * **.labels**: Issue tracker labels.
    * **.components**: Issue tracker components.
    * **.issue_metadata**: JSON with issue details (e.g., **{"priority": "High"}**).

**Processing**

* **Crashes**: Detected via **CrashResult** (non-zero return code or keywords like "segfault" in logs), with **crash-*** files uploaded if confirmed.
* **Stats**: Parsed from **stats-*.stats** and passed to **engine_common.get_testcase_run**.
* **Metadata**: Parsed by **engine_common.get_all_issue_metadata** and added to **fuzzer_metadata** for issue tracking.

**Troubleshooting**

* **No Crashes Detected**:
  * Check ***.log** files for crash keywords and ensure **fuzz.py** exits with a non-zero code on crashes.
  * The console output or the logs generate may be filtered out by the post fuzzing crash analyzer if the crash is ambiguous.
  * ```python
    new_crash_count, known_crash_count, processed_groups = process_crashes(
    ```
* **Missing Artifacts**: Verify **fuzz.py** writes to both **--crash_testcase_dir** and **--artifacts_dir**.
* **Metadata Ignored**: Ensure **engine_common.get_all_issue_metadata** recognizes your file extensions.
