# backend configuration
samples_path = 'results'
templates_path = 'samples'
base_path = '~/mounting_point/luckycat/'
temporary_path = '/tmp'

sample_generator_sleeptime = 0.1
crash_verification_sender_sleeptime = 10
job_scheduler_sleeptime = 60

# RabbitMQ configuration
queue_host = '127.0.0.1'

# database configuration
db_host = '127.0.0.1'
db_name = 'luckycat'
db_user = 'cat'
db_password = 'lucky'
db_port = 27017
debug = True

# frontend configuration
secret_key = 'this_is_f3c'
default_user_email = 'donald@great.again'
default_user_password = 'password'
default_user_api_key = 'yuL4uJ4loqCGl86NDwDloPaPa5PQZs0f9hXRrLjbnJNLau3vxWKs3qS0XKN7BV3o'

# mutation engine configuration
mutation_engines = [{'name': 'radamsa',
                     'description': 'radamsa is a test case generator for robustness testing',
                     'command': 'radamsa -m ft=2,fo=2,fn,num=5,td,tr2,ts1,tr,ts2,ld,lds,lr2,li,ls,lp,lr,lis,lrs,sr,sd,bd,bf,bi,br,bp,bei,bed,ber,uw,ui=2,ab -p nd=2 -o %OUTPUT% %INPUT% '},
                    {'name': 'urandom',
                     'description': 'just random bytes from /dev/urandom',
                     'command': 'dd if=/dev/urandom bs=64 count=1 > %OUTPUT%'},
                    {'name': 'external',
                     'description': 'fuzzer comes with its own external mutation engine',
                     'command': ''}]
maximum_samples = 4

# fuzzer configuration
fuzzers = [{'name': 'afl', 'description': 'AFL is a mutator and fuzzer'},
           {'name': 'cfuzz', 'description': 'cfuzz is a generic fuzzer that should run on all Unix-based targets'},
           {'name': 'qemufuzzer', 'description': 'qemufuzzer fuzzes binaries of whole firmware images'},
           {'name': 'elffuzzer', 'description': 'ELF fuzzer for *UNIX systems'},
           {'name': 'trapfuzzer', 'description': 'trap fuzzer for BSD-based systems'},
           {'name': 'syzkaller', 'description': 'Syzkaller is a mutator and fuzzer for Syscalls'},
           {'name': 'libFuzzer', 'description': 'LibFuzzer'}]

# fuzzer configuration
verifiers = [{'name': 'local_exploitable', 'description': 'Local exploitable verifier'},
             {'name': 'remote_exploitable', 'description': 'Remote exploitable verifier with gdb remote'},
             {'name': 'no_verification', 'description': 'No verification of crashes'}]

# Marker to indicate end of crash stacktrace. Anything after that is excluded
# from being stored as part of crash stacktrace (e.g. merge content, etc).
CRASH_STACKTRACE_END_MARKER = 'CRASH OUTPUT ENDS HERE'

# Skips using crash state similarity for these types.
CRASH_TYPES_WITH_UNIQUE_STATE = [
    {'name': 'Missing-library', 'description': 'missing library'},
    {'name': 'Out-of-memory', 'description': 'out of memory error'},
    {'name': 'Overwrites-const-input', 'description': ''},
    {'name': 'Timeout', 'description': ''}
]

# List of supported platforms.
PLATFORMS = [
    'LINUX',
    'ANDROID',
    'CHROMEOS',
    'MAC',
    'WINDOWS',
    'FUCHSIA',
    'ANDROID_KERNEL',
    'ANDROID_AUTO',
]

JobStates = [
    'started',
    'in-progress',
    'finished',
    'errored out'
]
