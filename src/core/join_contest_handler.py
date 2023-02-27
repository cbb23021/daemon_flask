import multiprocessing
import threading
import time
from datetime import datetime

from colorama import Fore
from common.const import Const
from common.data_cach import DataCache
from common.models import Contest
from common.utils.debugtool import DebugTool
from common.utils.orm_tool import ORMTool
from sqlalchemy import exc

from core.queue_handler import QueueHandler


class JoinContestHandler:

    @staticmethod
    def _show(msg, color=None, tag=None):
        color = color or str()
        tag = tag or 'INFO'
        print(
            f'{color}[{datetime.now().strftime("%F %X")}] [{tag.upper():5}] [ * {msg} ]{Fore.RESET}'
        )

    @classmethod
    def contest_id_monitor(cls):
        # 監聽 active_contest_ids
        active_contest = DataCache.get_active_contest_id()
        if active_contest:
            ORMTool.commit()
            active_contest_id = active_contest[1]
            contest = Contest.query.filter(
                Contest.id == active_contest_id,
                Contest.status == Const.ContestStatus.ACTIVATED,
            ).first()
            if not contest:
                DebugTool.warning(
                    msg=f'contest id {active_contest_id} not found or not activated'
                )
                DataCache.push_active_contest_ids(
                    contest_ids=[active_contest_id])
            else:
                cls._show(tag='log',
                          color=Fore.CYAN,
                          msg=f'>>>>> Active <contest:{active_contest_id}>')
                # 建立空注單
                QueueHandler.create_empty_orders(contest=contest)

                # 監聽 <contest_id>-USED, 接收注單更新至 order 及 member_fee_transaction
                threading.Thread(
                    target=QueueHandler.used_monitor,
                    name=f'<contest_id:{contest.id}>',
                    args=(contest.id, contest.open_datetime),
                    daemon=True,  # 主程式死掉後 同時刪除子程式的監聽
                ).start()
            time.sleep(1)

    @classmethod
    def new_contest_id_monitor(cls):
        time.sleep(1)  # Need run before new contest
        cls._show(tag='log',
                  color=Fore.GREEN,
                  msg=f'--- start listening new contests ---')
        while True:
            try:
                cls.contest_id_monitor()
            except exc.InterfaceError as e:
                cls._show(
                    tag='error',
                    color=Fore.RED,
                    msg='Packet sequence number wrong - got 102 expected 1')
                break
            except Exception as e:
                DebugTool.error(e)

    @classmethod
    def old_contest_id_monitor(cls):
        """ 監聽舊 contest orders (<contest_id>-USED) """
        old_contests = Contest.query.filter(
            Contest.status == Const.ContestStatus.ACTIVATED,
            Contest.settle_datetime.is_(None),
        ).all()

        contest_ids = [_.id for _ in old_contests]
        cls._show(tag='log',
                  color=Fore.GREEN,
                  msg=f'--- start listening old contests: {contest_ids} ---')

        threads = list()
        for contest in old_contests:
            thread = threading.Thread(
                target=QueueHandler.used_monitor,
                name=f'<contest_id:{contest.id}>',
                args=(contest.id, contest.open_datetime),
                daemon=True,  # 主程式死掉後 同時刪除子程式的監聽
            )
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

    @classmethod
    def _db_alive(cls):
        """
        sleep per 1 hr to keep db connect
        """
        while True:
            ORMTool.commit()
            time.sleep(60 * 60)

    @classmethod
    def exec(cls):
        """
        分別同時進行 新舊 contests 監聽
        """
        job_dict = dict()
        jobs = [
            cls.old_contest_id_monitor,
            cls.new_contest_id_monitor,
            cls._db_alive,
        ]
        while True:
            for job in jobs:
                if job.__name__ in job_dict:
                    continue
                process = multiprocessing.Process(target=job)
                process.start()
                job_dict.update({job.__name__: process})

            # 如果 new contest job 出錯 即重啟
            new_contest_job = job_dict[cls.new_contest_id_monitor.__name__]
            if not new_contest_job.is_alive():
                cls._show(tag='log',
                          color=Fore.LIGHTRED_EX,
                          msg=f'--- restart <jobs> after 2 sec ---')
                for job_name, process in job_dict.copy().items():
                    del job_dict[job_name]
                    process.terminate()
                    process.join()
                time.sleep(2)
