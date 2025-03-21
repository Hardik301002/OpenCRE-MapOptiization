import argparse
import os
import sys
import unittest
from typing import List

import click  # type: ignore
import coverage  # type: ignore
from flask_migrate import Migrate  # type: ignore

from application import create_app, sqla  # type: ignore

# Hacky solutions to make this both a command line application with argparse and a flask application

app = create_app(mode=os.getenv("FLASK_CONFIG") or "default")
migrate = Migrate(app, sqla, render_as_batch=True)


# flask <x> commands
@app.cli.command()  # type: ignore
@click.option(
    "--cover/--no-cover", default=False, help="Run tests under code coverage."
)  # type: ignore
@click.argument("test_names", nargs=-1)  # type: ignore
def test(cover: coverage.Coverage, test_names: List[str]) -> None:
    COV = None
    if cover or os.environ.get("FLASK_COVERAGE"):
        COV = coverage.coverage(
            branch=True,
            include="application/*",
            check_preimported=True,
            config_file="application/tests/.coveragerc",
        )
        COV.start()
        # Hack to get coverage to cover method and class defs
        from application import create_app, sqla  # type: ignore
        from application.cmd import cre_main

    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover("application/tests", pattern="*_test.py")
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print("Coverage Summary:")
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, "tmp/coverage")
        COV.html_report(directory=covdir)
        print("HTML version: file://%s/index.html" % covdir)
        COV.erase()


# python cre.py --<x> commands


def main() -> None:
    app_context = app.app_context()
    app_context.push()

    script_path = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(
        description="Add documents describing standards to a database"
    )
    parser.add_argument(
        "--add",
        action="store_true",
        help="will treat the incoming spreadsheet as a reviewed cre and add to the database",
    )
    # parser.add_argument(
    #     "--review",
    #     action="store_true",
    #     help="will treat the incoming spreadsheet as a new mapping, will try to map the incoming connections to existing cre\
    #         and will create a new spreadsheet with the result for review. Nothing will be added to the database at this point",
    # )
    parser.add_argument(
        "--email",
        help="used in conjuctions with --review, what email to share the resulting spreadsheet with",
        default="standards_cache.sqlite",
    )
    parser.add_argument(
        "--from_spreadsheet", help="import from a spreadsheet to yaml and then database"
    )
    parser.add_argument(
        "--print_graph",
        help="will show the graph of the relationships between standards",
    )
    parser.add_argument(
        "--cache_file",
        help="where to read/store data",
        default=os.path.join(script_path, "standards_cache.sqlite"),
    )
    parser.add_argument(
        "--cre_loc",
        default=os.path.join(os.path.dirname(os.path.realpath(__file__)), "./cres/"),
        help="define location of local cre files for review/add",
    )
    parser.add_argument(
        "--owasp_proj_meta",
        default=None,
        help="define location of owasp project metadata",
    )
    parser.add_argument(
        "--osib_in",
        default=None,
        help="define location of local osib file for review/add",
    )
    parser.add_argument(
        "--osib_out",
        default=None,
        help="define location of local directory to export database in OSIB format to",
    )
    # Start External Project importing
    parser.add_argument(
        "--zap_in",
        action="store_true",
        help="import zap alerts by cloning zap's website and parsing the alert .md files",
    )
    parser.add_argument(
        "--cheatsheets_in",
        action="store_true",
        help="import cheatsheets by cloning the repo website and parsing the .md files",
    )
    parser.add_argument(
        "--github_tools_in",
        action="store_true",
        help="import supported github tools, urls can be found in misc_tools_parser.py",
    )
    parser.add_argument(
        "--capec_in",
        action="store_true",
        help="import CAPEC",
    )
    parser.add_argument(
        "--cwe_in",
        action="store_true",
        help="import CWE",
    )

    parser.add_argument(
        "--csa_ccm_v3_in",
        action="store_true",
        help="import CSA's CCM v3 from https://docs.google.com/spreadsheets/d/1b5i8OV919aiqW2KcYWOQvkLorL1bRPqjthJxLH0QpD8",
    )
    parser.add_argument(
        "--csa_ccm_v4_in",
        action="store_true",
        help="import CSA's CCM v4 from https://docs.google.com/spreadsheets/d/1QDzQy0wt1blGjehyXS3uaHh7k5OOR12AWgAA1DeACyc",
    )
    parser.add_argument(
        "--iso_27001_in",
        action="store_true",
        help="import ISO 27001 by using the NIST mappings located at https://csrc.nist.gov/CSRC/media/Publications/sp/800-53/rev-5/final/documents/sp800-53r5-to-iso-27001-mapping.docx",
    )
    parser.add_argument(
        "--owasp_secure_headers_in",
        action="store_true",
        help="import owasp secure headers",
    )
    parser.add_argument(
        "--pci_dss_3_2_in",
        action="store_true",
        help="import pci dss from https://www.compliancequickstart.com/",
    )
    parser.add_argument(
        "--pci_dss_4_in",
        action="store_true",
        help="import pci dss from https://www.compliancequickstart.com/",
    )
    parser.add_argument(
        "--juiceshop_in",
        action="store_true",
        help="import juiceshop challenges from their repo",
    )
    parser.add_argument(
        "--dsomm_in",
        action="store_true",
        help="import dsomm from their repo (https://raw.githubusercontent.com/devsecopsmaturitymodel/DevSecOps-MaturityModel-data/main/src/assets/YAML/generated/generated.yaml)",
    )
    parser.add_argument(
        "--cloud_native_security_controls_in",
        action="store_true",
        help="import cloud native security controls from their repo (https://raw.githubusercontent.com/cloud-native-security-controls/controls-catalog/main/controls/controls_catalog.csv)",
    )
    # End External Project importing

    parser.add_argument(
        "--import_external_projects",
        action="store_true",
        help="import all external projects, shortcut for calling all of *_in",
    )
    parser.add_argument(
        "--generate_embeddings",
        action="store_true",
        help="for every node, download the text pointed to by the hyperlink and generate embeddings for the content of the specific node",
    )
    parser.add_argument(
        "--populate_neo4j_db",
        action="store_true",
        help="populate the neo4j db",
    )
    parser.add_argument(
        "--start_worker",
        action="store_true",
        help="start redis queue worker",
    )
    parser.add_argument(
        "--preload_map_analysis_target_url",
        default="",
        help="preload map analysis for all possible 2 standards combinations, use target url as an OpenCRE base",
    )
    parser.add_argument(
        "--delete_map_analysis_for",
        default="",
        help="delete all map analyses for resource spcified",
    )
    parser.add_argument(
        "--delete_resource",
        default="",
        help="delete all the mappings, embeddings and gap analysis for the resource",
    )
    parser.add_argument(
        "--upstream_sync",
        action="store_true",
        help="download the cre graph from upstream",
    )

    args = parser.parse_args()

    from application.cmd import cre_main

    cre_main.run(args)


if __name__ == "__main__":  # if we're called directly
    main()
