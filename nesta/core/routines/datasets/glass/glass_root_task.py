"""
[AutoML] Topic modelling (CorEx)
================================

Automated topic modelling of arXiv articles via the CorEx
algorithm. See :obj:`topic_process_task_chain.json`
for the full processing chain, but in brief:
Vectorization is performed, followed by n-gramming
(a lookup via Wiktionary) and then topics via CorEx.
"""

import luigi
import os
import datetime
import json
import logging

from nesta.core.luigihacks import s3
from nesta.core.luigihacks.automl import AutoMLTask
from nesta.core.luigihacks.parameter import DictParameterPlus


S3PATH = 'nesta-glass-ai/sic-classifer'
CHAIN_FILE = 'sic_task_chain.json'
THIS_PATH = os.path.dirname(os.path.realpath(__file__))
CHAIN_PARAMETER_PATH = os.path.join(THIS_PATH, CHAIN_FILE)


class DummyInputTask(luigi.ExternalTask):
    '''Dummy task acting as the single input data source'''
    def output(self):
        '''Points to the S3 Target'''
        return s3.S3Target(f'{S3PATH}/input.json')


class RootTask(luigi.Task):
    s3_path_prefix = luigi.Parameter(default=f's3://{S3PATH}')
    date = luigi.DateParameter(default=datetime.datetime.now())
    production = luigi.BoolParameter(default=False)
    grid_task_kwargs = DictParameterPlus(default={})

    def requires(self):
        s3_path_prefix = f'{self.s3_path_prefix}/automl/{self.date}'
        s3_path_out = f'{s3_path_prefix}/outputs'
        return AutoMLTask(s3_path_prefix=s3_path_prefix,
                          task_chain_filepath=CHAIN_PARAMETER_PATH,
                          test=not self.production,
                          input_task=DummyInputTask,
                          input_task_kwargs={'s3_path_out': s3_path_out,
                                             'test': not self.production,
                                             'grid_task_kwargs': self.grid_task_kwargs})

    def run(self):
        # Generate the grid of results

        # Load the input data (note the input contains the path
        # to the output)
        # _body = self.input().open("rb")
        # _filename = _body.read().decode('utf-8')
        # obj = s3.S3Target(f"{self.raw_s3_path_prefix}/"
        #                   f"{_filename}").open('rb')
        # data = json.load(obj)

        # # Touch the output
        # self.output().touch()
        pass