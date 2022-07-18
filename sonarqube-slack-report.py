import requests, json, os, time, sys
from lxml.html import fromstring


class SonarQubeReportSlack:

    def __init__(self):
        self.slack_token = os.getenv("slack_token")
        self.fail_build = os.getenv("fail_build", "false")
        self.component = os.getenv("component")
        self.slack_channel = os.getenv("slack_channel")
        self.sonar_url = os.getenv("sonar_url")
        self.sonar_username = os.getenv("sonar_username")
        self.sonar_password = os.getenv("sonar_password")

    def wait_for_analysis(self):
        ATTEMPTS = 10
        url = self.sonar_url + "/api/ce/component?component=%s" % (self.component,)
        while True:
            res = requests.get(url, auth=(self.sonar_username, self.sonar_password)).json()
            if "queue" not in res.keys() or not res["queue"] or ATTEMPTS == 0:
                break
            time.sleep(10)
            ATTEMPTS -= 1

    def generate_summary_and_report(self):
        cmd = """sonar-report  --sonarurl="%s" --sonarusername="%s" --sonarpassword="%s"  --sonarcomponent="%s" --allbugs="false" > sonar_report.html"""
        cmd = cmd % (self.sonar_url, self.sonar_username, self.sonar_password, self.component)
        os.system(cmd)
        with open('sonar_report.html') as f: report = f.read()
        count, summary = self.generate_summary(report)
        slack_status = self.post_file_to_slack(
            summary,
            'Report.html',
            report)
        # Block Build in case of blocker
        if int(count) > 1 and self.fail_build == "true":
            sys.exit(1)

    def generate_summary(self, report):
        count = 0
        stable = ""
        html_str = fromstring(report)
        issues = html_str.xpath("//div[@class='summup']//tr/td/text()")
        isitr = iter(issues)
        issues_dict = dict(zip(isitr, isitr))
        print("::set-output name=summary_table::%s" % self.get_summary_table(issues_dict))
        count = int(issues_dict.get("BLOCKER",0))+int(issues_dict.get("CRITICAL",0))
        return count, "SAST %s: %s Blocker/Critical Issues Identified in the Repository" % (self.component, str(count))

    def post_file_to_slack(
            self, text, file_name, file_bytes, file_type=None, title='SonarQube Vulnerability Report '
    ):
        return requests.post(
            'https://slack.com/api/files.upload',
            {
                'token': self.slack_token,
                'filename': file_name,
                'channels': self.slack_channel,
                'filetype': file_type,
                'initial_comment': text,
                'title': title
            },
            files={'file': file_bytes}).json()

    def get_summary_table(self, issues_dict):
        return """
        | Severity | Number of Issues |
        | --- | --- |
        | BLOCKER | %s   |
        | CRITICAL | %s   |
        | MAJOR | %s   |
        | MINOR | %s  |
        """%(issues_dict.get("BLOCKER","0"),
             issues_dict.get("CRITICAL","0"),
             issues_dict.get("MAJOR","0"),
             issues_dict.get("MINOR","0"))
    
    def run(self):
        self.wait_for_analysis()
        self.generate_summary_and_report()


SonarQubeReportSlack().run()
