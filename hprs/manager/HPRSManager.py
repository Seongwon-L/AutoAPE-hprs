# -*- coding: utf-8 -*-
# Author : Jin Kim
# e-mail : jin.kim@seculayer.com
# Powered by Seculayer © 2021 AI Service Model Team, R&D Center.
import http.client
import json
from typing import List, Dict
import time

from hprs.common.utils.Utils import Utils
from hprs.common.Common import Common
from hprs.common.Constants import Constants
from hprs.manager.SFTPClientManager import SFTPClientManager
from hprs.recommender.RandomRecommender import RandomRecommender


class HPRSManager(object):
    # class : DataAnalyzerManager
    def __init__(self, job_id, job_idx):
        self.logger = Common.LOGGER.get_logger()

        self.mrms_sftp_manager: SFTPClientManager = SFTPClientManager(
            "{}:{}".format(Constants.MRMS_SVC, Constants.MRMS_SFTP_PORT), Constants.MRMS_USER, Constants.MRMS_PASSWD)

        self.http_client: http.client.HTTPConnection = http.client.HTTPConnection(
            Constants.MRMS_SVC, Constants.MRMS_REST_PORT)

        self.job_id = job_id
        self.current = 0
        self.logger.info("HPRSManager initialized.")

    def load_job_info(self, filename):
        return self.mrms_sftp_manager.load_json_data(filename)

    def recommend(self):
        filename = "{}/MARS_{}_{}.info".format(Constants.DIR_DIVISION_PATH, self.job_id, self.current)
        if self.mrms_sftp_manager.is_exist(filename):
            job_info = self.load_job_info(filename)
            results = RandomRecommender().recommend(job_info, self.job_id)
            self.logger.info(f"Recommended {len(results)} elements")

            self.http_client.request("POST", "/mrms/insert_ml_param_info", body=json.dumps(results))
            response = self.http_client.getresponse()
            self.logger.info("{} {} {}".format(response.status, response.reason, response.read()))

            learn_hist_list = self.make_learn_hist(results)
            for learn_hist in learn_hist_list:
                time.sleep(0.2)
                self.http_client.request("POST", "/mrms/insert_learn_hist", body=json.dumps(learn_hist))
                response = self.http_client.getresponse()
                self.logger.info("{} {} {}".format(response.status, response.reason, response.read()))

            f = self.mrms_sftp_manager.get_client().open(
                "{}/HPRS_{}_{}.info".format(Constants.DIR_DIVISION_PATH, self.job_id, self.current),
                "w"
            )
            f.write(json.dumps(results, indent=2))

            time.sleep(0.2)
            status = {"status": "6", "project_id": self.job_id}
            self.http_client.request("POST", "/mrms/update_projects_status", body=json.dumps(status))
            response = self.http_client.getresponse()
            self.logger.info("{} {} {}".format(response.status, response.reason, response.read()))
            f.close()
            self.current += 1

    def get_terminate(self) -> bool:
        self.http_client.request("GET", "/mrms/get_proj_sttus_cd?project_id={}".format(self.job_id))
        response = self.http_client.getresponse()
        status = response.read().decode("utf-8")
        if status == Constants.STATUS_PROJECT_COMPLETE or status == Constants.STATUS_PROJECT_ERROR:
            return True
        return False

    def make_learn_hist(self, ml_param_dict_list: List[Dict]):
        for ml_param_dict in ml_param_dict_list:
            ml_param_dict["learn_hist_no"] = self.get_uuid()
            ml_param_dict["learn_sttus_cd"] = "1"
            ml_param_dict["start_time"] = Utils.get_current_time()

        return ml_param_dict_list

    def get_uuid(self):
        self.http_client.request("GET", "/mrms/get_uuid")
        response = self.http_client.getresponse()
        return response.read().decode("utf-8").replace("\n", "")


if __name__ == '__main__':
    dam = HPRSManager("ID", "0")
