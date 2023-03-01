import os

from flask import Flask, redirect, render_template
from flask_security import login_required

from frontend.api.CrashApi import crash_api
from frontend.api.TestCaseVariantApi import testcase_variants_api
from frontend.api.TrialApi import trial_api
from src.frontend.api.BotApi import bots_api
from src.frontend.api.BuildMetadataApi import BuildMetadata_api
from src.frontend.api.DataBundleAPI import DataBundle_api
from src.frontend.api.FuzzTargetApi import fuzztargets_api
from src.frontend.api.FuzzTargetJobApi import fuzzTargetJobs_api
from src.frontend.api.JobsApi import jobs_api
from src.frontend.api.TasksApi import tasks_api
from src.frontend.api.TestCaseApi import testcases_api
from src.frontend.api.FuzzerApi import fuzzers_api
from src.frontend.handlers.Crashes import crashes
from src.frontend.handlers.Jobs import jobs
from src.frontend.handlers.Users import users
from src.frontend.api.StatisticsApi import statistics_api
from src.frontend.handlers.Statistics import statistics
from src.frontend.handlers.jinja2_custom import exploitable_color, map_signal_to_string
from src.frontend.security.init_security import add_flask_security
from flask_swagger_ui import get_swaggerui_blueprint

from src.database.database import db


def configure_app():
    app.config['DEBUG'] = global_config.debug
    app.config['MONGODB_DB'] = global_config.db_name
    app.config['MONGODB_HOST'] = global_config.db_host
    app.config['MONGODB_PORT'] = global_config.db_port
    app.config['mutation_engines'] = global_config.mutation_engines
    app.config['fuzzers'] = global_config.fuzzers
    app.config['verifiers'] = global_config.verifiers
    app.config['maximum_samples'] = global_config.maximum_samples
    app.config["secret_key"] = global_config.secret_key
    app.config["default_user_api_key"] = global_config.default_user_api_key
    app.config["queue_host"] = global_config.queue_host


app = Flask(__name__)
env = os.environ.get("ENV")
if env == "LOCAL":
    from src import local_global_config as global_config
elif env == "DOKER":
    from src import docker_global_config as global_config
else:
    from src import local_global_config as global_config

configure_app()

db.init_app(app)
add_flask_security(app)

### API registrtion ###
app.register_blueprint(jobs_api)
app.register_blueprint(jobs)
app.register_blueprint(crashes)
app.register_blueprint(users)
app.register_blueprint(statistics_api)
app.register_blueprint(statistics)
app.register_blueprint(testcases_api)
app.register_blueprint(tasks_api)
app.register_blueprint(fuzzers_api)
app.register_blueprint(bots_api)
app.register_blueprint(fuzztargets_api)
app.register_blueprint(fuzzTargetJobs_api)
app.register_blueprint(BuildMetadata_api)
app.register_blueprint(DataBundle_api)
app.register_blueprint(crash_api)
app.register_blueprint(testcase_variants_api)
app.register_blueprint(trial_api)

app.jinja_env.globals.update(exploitable_color=exploitable_color)
app.jinja_env.globals.update(map_signal_to_string=map_signal_to_string)

### swagger specific ###
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "LuckyCat"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)


### end swagger specific ###


@app.route("/")
@app.route("/home")
def index():
    return render_template("home.html")


@app.route("/about")
@login_required
def about():
    return render_template("about.html")


@app.route("/logout")
@login_required
def logout():
    return redirect("/home")
