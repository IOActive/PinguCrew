# Glossary

This page provides a glossary of what certain terms mean in the context of PinguCrew.

## Bot

A machine which runs Pingucrew [tasks](#task).

## Corpus

A set of inputs for a [fuzz target](#fuzz-target). In most contexts, it refers to a set of minimal test inputs that generate maximal code coverage.

## Corpus pruning

A task which takes a [corpus](#corpus) and removes unnecessary inputs while maintaining the same code coverage.

## Crash state

A signature that we generate from the crash stacktrace for deduplication purposes.

## Crash type

The type of a crash. PinguCrew uses this to determine the severity.

For security vulnerabilities this may be (but not limited to):

- Bad-cast
- Heap-buffer-overflow
- Heap-double-free
- Heap-use-after-free
- Stack-buffer-overflow
- Stack-use-after-return
- Use-after-poison

Other crash types include:

- Null-dereference
- Timeout
- Out-of-memory
- Stack-overflow
- ASSERT

## Fuzz target

A function or program that accepts an array of bytes and does something interesting with these bytes using the API under test. See the [libFuzzer documentation](https://llvm.org/docs/LibFuzzer.html#fuzz-target) for a more detailed explanation. A fuzz target is typically given the array of bytes by [libFuzzer][libFuzzer] or [AFL][AFL] for coverage guided fuzzing.

## Fuzzer

A program which generates/mutates inputs of a certain format for testing a target program. For example, this may be a program which generates valid JavaScript testcases for fuzzing an JavaScript engine such as V8.

## Fuzzing engine

A tool used for performing coverage guided fuzzing. The fuzzing engine typically mutates inputs, gets coverage information, and adds inputs to the corpus based on new coverage information. PinguCrew supports the fuzzing engines [libFuzzer][libFuzzer] and [AFL][AFL].

## Job type

A specification for how to run a particular target program for fuzzing, and where the builds are located. Consists of environment variable values.

## Minimization

A [task](#task) that tries to minimize a [testcase](#testcase) to its smallest possible size, such that it still triggers the same underlying bug on the target program.

## Reliability of reproduction

A crash is reliably reproducible if the target program consistently crashes with the same [crash state](#crash-state) for the given input.

## Regression range

A range of commits in which the bug was originally introduced.

## Revision

A number (not a git hash) that can be used to identify a particular build. This number should increment with every source code revision.

## Sanitizer

A [dynamic testing](https://en.wikipedia.org/wiki/Dynamic_testing) tool that uses compile-time instrumentation to detect bugs during program execution.

Examples:

* [ASan][ASan] (aka AddressSanitizer)
* [LSan](https://clang.llvm.org/docs/LeakSanitizer.html) (aka LeakSanitizer)
* [MSan](https://clang.llvm.org/docs/MemorySanitizer.html) (aka MemorySanitizer)
* [UBSan](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html) (aka UndefinedBehaviorSanitizer)
* [TSan](https://clang.llvm.org/docs/ThreadSanitizer.html) (aka ThreadSanitizer)

Sanitizers are best supported by the [Clang][Clang] compiler. [ASan][ASan], or AddressSanitizer, is usually the most important sanitizer as it reveals the most memory corruption bugs.

## Task

A unit of work to be performed by a [bot](#bot), such as a fuzzing session or minimizing a testcase. A task has the following data structure:

```json
{
  'job_id': 112432354325',
  'platform': 'linux',
  'command': 'command',
  'argument': '',
}
```

Commands:

```json
COMMAND_MAP = {
    'analyze': analyze_task,
    'blame': blame_task,
    'corpus_pruning': corpus_pruning_task,
    'fuzz': fuzz_task,
    'impact': impact_task,
    'minimize': minimize_task,
    'train_rnn_generator': train_rnn_generator_task,
    'progression': progression_task,
    'regression': regression_task,
    'symbolize': symbolize_task,
    'unpack': unpack_task,
    'upload_reports': upload_reports_task,
    'variant': variant_task,
}
```

---

## Testcase

An input for the target program that causes a crash or bug. On a testcasedetails page, you can download a "Minimized Testcase" or "Unminimized Testcase",
these refer to the input that needs to be passed to the target program.
