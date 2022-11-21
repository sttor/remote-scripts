import requests, json, os, time, sys
from lxml.html import fromstring


class SonarQubeReportSlack:

    def __init__(self):
        self.component = os.getenv("PROJECT_KEY")
        self.sonar_url = os.getenv("SONAR_HOST_URL")
        self.sonar_token = os.getenv("SONAR_TOKEN")


    def generate_summary_and_report(self):
        cmd = """sonar-report  --sonarurl="%s" --sonartoken="%s"  --sonarcomponent="%s" """
        cmd = cmd % (self.sonar_url, self.sonar_token, self.component)
        os.system(cmd)
        with open('report.html') as f: report = f.read()
        count, summary, summarytable = self.generate_summary(report)
        print("::set-output name=summarytable::%s" % summarytable)
        print("::set-output name=summary::%s" % summary)

    def generate_summary(self, report):
        html_str = fromstring(report)
        issues = html_str.xpath("//div[@class='summup']//tr/td/text()")
        isitr = iter(issues)
        issues_dict = dict(zip(isitr, isitr))
        summary_table = self.get_summary_table(issues_dict)
        count = int(issues_dict.get("BLOCKER", 0)) + int(issues_dict.get("CRITICAL", 0))
        return count, "SAST %s: %s Blocker/Critical Issues Identified in the Repository" % (
        self.component, str(count)), summary_table

    def get_summary_table(self, issues_dict):
        return "| Severity | Number of Issues |%0A| --- | --- |%0A| BLOCKER | {blocker} " \
               "  |%0A| CRITICAL | {critical}   |%0A| MAJOR | {major} " \
               " |%0A| MINOR | {minor}  |".format(blocker=issues_dict.get("BLOCKER", "0"),
                                                  critical=issues_dict.get("CRITICAL", "0"),
                                                  major=issues_dict.get("MAJOR", "0"),
                                                  minor=issues_dict.get("MINOR", "0"))

    def run(self):
        self.generate_summary_and_report()


SonarQubeReportSlack().run()
