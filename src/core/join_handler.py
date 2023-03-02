import multiprocessing
import threading
import time
from datetime import datetime

from colorama import Fore
from sqlalchemy import exc

from common.const import Const
from common.models import LottoDraw
from common.utils.data_cache import DataCache
from common.utils.debugtool import DebugTool
from common.utils.orm_tool import ORMTool
from core.queue_handler import QueueHandler


class JoinHandler:

    @staticmethod
    def _show(msg, color=None, tag=None):
        color = color or str()
        tag = tag or 'INFO'
        print(
            f'{color}[{datetime.now().strftime("%F %X")}] [{tag.upper():5}] [ * {msg} ]{Fore.RESET}'
        )

    @classmethod
    def id_monitor(cls):
        # 監聽 active_draw_ids
        active_draw = DataCache.get_active_draw_id()
        if active_draw:
            ORMTool.commit()
            active_draw_id = active_draw[1]
            draw = LottoDraw.query.filter(
                LottoDraw.id == active_draw_id,
                LottoDraw.status == Const.DrawStatus.ACTIVATED,
            ).first()
            if not draw:
                DebugTool.warning(
                    msg=f'<draw:{active_draw_id}> not found or not activated')
                DataCache.push_active_draw_ids(draw_ids=[active_draw_id])
            else:
                cls._show(tag='log',
                          color=Fore.CYAN,
                          msg=f'>>>>> Active <draw:{active_draw_id}>')
                # 建立空注單
                QueueHandler.create_empty_orders(draw=draw)

                # 監聽 <draw_id>-USED, 接收注單更新至 order 及 member_fee_transaction
                threading.Thread(
                    target=QueueHandler.used_monitor,
                    name=f'<draw:{draw.id}>',
                    args=(draw.id, draw.open_dt),
                    daemon=True,  # 主程式死掉後 同時刪除子程式的監聽
                ).start()
            time.sleep(1)

    @classmethod
    def new_id_monitor(cls):
        time.sleep(1)  # Need run before new draw
        cls._show(tag='log',
                  color=Fore.GREEN,
                  msg='--- start listening new draws ---')
        while True:
            try:
                cls.id_monitor()
            except exc.InterfaceError as e:
                cls._show(
                    tag='error',
                    color=Fore.RED,
                    msg='Packet sequence number wrong - got 102 expected 1')
                break
            except Exception as e:
                DebugTool.error(e)

    @classmethod
    def old_id_monitor(cls):
        """ 監聽舊 orders (<draw_id>-USED) """
        old_draws = LottoDraw.query.filter(
            LottoDraw.status == Const.DrawStatus.ACTIVATED,
            LottoDraw.settle_dt.is_(None),
        ).all()

        draw_ids = [_.id for _ in old_draws]
        cls._show(tag='log',
                  color=Fore.GREEN,
                  msg=f'--- start listening old draws: {draw_ids} ---')

        threads = list()
        for draw in old_draws:
            thread = threading.Thread(
                target=QueueHandler.used_monitor,
                name=f'<draw_id:{draw.id}>',
                args=(draw.id, draw.open_dt),
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
        分別同時進行 新舊 draw 監聽
        """
        job_dict = dict()
        jobs = [
            cls.old_id_monitor,
            cls.new_id_monitor,
            cls._db_alive,
        ]
        while True:
            for job in jobs:
                if job.__name__ in job_dict:
                    continue
                process = multiprocessing.Process(target=job)
                process.start()
                job_dict.update({job.__name__: process})

            # 如果 new draw job 出錯 即重啟
            new_job = job_dict[cls.new_id_monitor.__name__]
            if not new_job.is_alive():
                cls._show(tag='log',
                          color=Fore.LIGHTRED_EX,
                          msg='--- restart <jobs> after 2 sec ---')
                for job_name, process in job_dict.copy().items():
                    del job_dict[job_name]
                    process.terminate()
                    process.join()
                time.sleep(2)
