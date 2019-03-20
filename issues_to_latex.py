from jira.client import JIRA
import yaml

class IssuesToLatex:
    def __init__(self):
        with open('issues_to_latex_config.yaml') as f:
            data = yaml.safe_load(f)

        self._username = data['login']['username']
        self._password = data['login']['password']

        self._project = data['project_info']['project']
        self._team = data['project_info']['team']
        self._start_date = data['tasks_info']['startdate']
        self._end_date = data['tasks_info']['enddate']

        # resolution types = Fixed, Won't Fix, Done, Won't Do, No longer required by client,
        # Duplicate, Incomplete, cannot reproduce, moved to development
        self._accepted_resolutions = data['tasks_info']['resolutions']

        self._jira = None
        self._custom_fields = {
            'customer_summary': 'customfield_10300',
            'customer_report': 'customfield_10600',
            'epic_key': 'customfield_10006',
            'epic_name': 'customfield_10007',
        }
        self._issues_to_latex()

    def _issues_to_latex(self):
        options = {'server': 'https://eden.esss.com.br/jira/'}
        basic_auth = (self._username, self._password)
        self._jira = JIRA(basic_auth=basic_auth, options=options, )
        issues = self._search_issues()

        with open('issues_to_latex.txt', 'w', encoding='utf-8') as f:

            application_issues = []
            calc_issues = []
            unknown = []
            needs_review = []

            for issue in issues:
                if issue.fields.resolution.name not in self._accepted_resolutions:
                    continue

                key, customer_summary, customer_report, epic_name = self._parse_issue(issue)

                issue_needs_review = customer_summary is None or customer_report is None or \
                                     len(issue.fields.components) == 0 or len(customer_summary) < 3

                if customer_report:
                    words = customer_report.split()
                    for index, word in enumerate(words):
                        if index == 0 and word[0].isupper():    # lower first char of customer report
                            word = word[:1].lower() + word[1:]

                        words[index] = self._remove_string_format(word)

                    customer_report = " ".join(words)
                    if customer_report[-1] == ".":     # remove period
                        customer_report = customer_report[:-1]

                report_item = "\\item \\textbf{{{}}}: {}".format(issue.key, customer_summary)
                report_item += ": {};".format(customer_report) if customer_report else ";"
                element = (epic_name, report_item)

                if issue_needs_review:
                    needs_review.append(element)
                elif issue.fields.components[0].name == "Application":
                    application_issues.append(element)
                elif issue.fields.components[0].name == "Numerical":
                    calc_issues.append(element)
                else:
                    unknown.append(element)  # crazy RF-DAP components

            self._sort_by_epic_name(application_issues)
            self._sort_by_epic_name(calc_issues)
            self._sort_by_epic_name(needs_review)
            self._sort_by_epic_name(unknown)

            lines = []
            if application_issues:
                self._add_issues(lines, application_issues, "Application")
            if calc_issues:
                self._add_issues(lines, calc_issues, "Numeric")
            if needs_review:
                self._add_issues(lines, needs_review, "Needs review")
            if unknown:
                self._add_issues(lines, unknown, "UNKNOWN")

            f.write('\n'.join(lines))

    def _parse_issue(self, issue):
        customer_summary = getattr(issue.fields, self._custom_fields['customer_summary'], None)
        customer_report = getattr(issue.fields, self._custom_fields['customer_report'], None)

        if customer_report and \
            "could you briefly describe what has been done to resolve this issue?" in str.lower(customer_report):
            customer_report = ''

        epic_key = getattr(issue.fields, self._custom_fields['epic_key'], None)
        epic_name = "No Epic"
        if epic_key:
            epic_name = getattr(self._jira.issue(epic_key).fields, self._custom_fields['epic_name'], "No Epic")

        return issue.key, customer_summary, customer_report, epic_name


    def _search_issues(self):
        team = ", ".join(self._team)
        jql_str = f"project = {self._project} AND status in (Resolved, Closed) AND assignee in ({team}) AND " \
            f"issuetype in (Bug, Improvement, Story, Task, Support, Sub-task) AND " \
            f"resolutiondate >= {self._start_date} AND resolutiondate <= {self._end_date} ORDER BY component ASC, resolved ASC"

        return self._jira.search_issues(jql_str, maxResults=False)

    def _remove_string_format(self, word):
        has_changed = False
        while word:
            if word[0] in ("{", "*", "_", "}"):
                word = word[1:]
                has_changed = True
            else:
                if word[-1] in ("{", "*", "_", "}"):
                    word = word[:-1]
                    has_changed = True
                else:
                    break

        return word if not has_changed else "\\textit{{{}}}".format(word)

    def _sort_by_epic_name(self, elements):
        '''
        :param List[Tuple[epic_name, report_item] elements:
        '''
        elements.sort(key=lambda tup: tup[0] if tup[0] is not None else "No Epic")

    def _add_issues(self, lines, epic_report_list, component):
        '''
        :param lines:
            current list to add items

        :param List[Tuple[epic_name, report_item] epic_report_list:

        :param str component:
            "Application", "Numeric" or crazy RF-DAP components
        '''
        lines += ["", "", "% ------------------ " + component + "---------------------"]
        current_epic = ''
        for epic, report_item in epic_report_list:
            if epic != current_epic:
                lines += ["", epic, ""]
                current_epic = epic

            lines.append(report_item if report_item is not None else "None")


IssuesToLatex()



