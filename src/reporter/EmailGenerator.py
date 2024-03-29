# Copyright 2024 IOActive
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tabulate import tabulate

class EmailGenerator:
    def process_stats_to_tabular_output(self, stats):
        output = ''
        for job in stats:
            tabulate_input = []
            tabulate_input.append(["Job", job['Job'], ''])
            for key,value in job['stats'].items():
                row = [key]
                for key, value in job['stats'][key].items():
                    row.append(key)
                    row.append(value)
                    tabulate_input.append(row)
                    row=['']
            output += tabulate(tabulate_input, headers='firstrow', tablefmt='fancy_grid') + '\n\n'
        return output


