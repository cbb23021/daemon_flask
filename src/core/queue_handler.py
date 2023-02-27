from datetime import datetime, timedelta

from colorama import Fore

from app import db
from common.const import Const
from common.data_cache import DataCache
from common.models import Order
from common.utils.debugtool import DebugTool
from common.utils.orm_tool import ORMTool
from common.utils.transaction_tool import TransactionTool


class QueueHandler:

    @staticmethod
    def _show(msg, color=None, tag=None):
        color = color or str()
        tag = tag or 'INFO'
        print(
            f'{color}[{datetime.now().strftime("%F %X")}] [{tag.upper():5}] [ * {msg}]{Fore.RESET}'
        )

    @classmethod
    def create_empty_orders(cls, contest):
        """ 建立空注單 並將order_id存入<contest_id>-WAIT中 """
        obj_list = list()
        contest_size = contest.criterion.contest_size
        for _ in range(contest_size):
            order = Order(
                sport_id=contest.sport_id,
                match_id=contest.match_id,
                contest_id=contest.id,
                status=Const.OrderType.PENDING,
            )
            obj_list.append(order)
        db.session.bulk_save_objects(obj_list, return_defaults=True)
        db.session.flush()
        db.session.commit()
        obj_ids_list = [obj.id for obj in obj_list]

        # 檢查空注單是否全部新增完成，若否 則確認miss幾張後補建立
        while True:
            if len(obj_ids_list) == contest_size:
                break
            missing_contest_size = contest_size - len(obj_ids_list)
            missing_obj_list = list()
            for _ in range(missing_contest_size):
                order = Order(
                    sport_id=contest.sport_id,
                    match_id=contest.match_id,
                    contest_id=contest.id,
                    status=Const.OrderType.PENDING,
                )
                missing_obj_list.append(order)
            db.session.bulk_save_objects(missing_obj_list,
                                         return_defaults=True)
            db.session.flush()
            for obj in missing_obj_list:
                obj_ids_list.append(obj)
        db.session.commit()

        DataCache.push_order_data_to_wait(contest_id=contest.id,
                                          value=obj_ids_list)
        cls._show(
            tag='order',
            msg=f'Init empty order done. <contest:{contest.id}> by nums: {len(obj_ids_list)}'
        )

    @classmethod
    def used_monitor(cls, contest_id, open_datetime):
        """
            pop data from <contest_id>-WAIT
            format => order_id:member_id:cash:ticket
        """
        while True:
            cancel_contest_ids = DataCache.get_cancel_contest_signal()
            if str(contest_id) in cancel_contest_ids:
                cls._show(tag='log',
                          color=Fore.YELLOW,
                          msg=f'>>>>> Cancel <contest:{contest_id}>')
                DataCache.del_cancel_contest_signal(contest_id=contest_id)
                return True

            if datetime.now() > open_datetime + timedelta(hours=5):
                cls._show(tag='log',
                          color=Fore.YELLOW,
                          msg=f'>>>>> Stop Listen 5hr <contest:{contest_id}>')
                return True

            order_data = DataCache.get_used_order_data(contest_id=contest_id)
            if order_data:
                order_id, member_id, cash, ticket = order_data[1].split(':')
                order_id, member_id, cash, ticket = int(order_id), int(
                    member_id), int(cash), int(ticket)
                cls._show(
                    tag='order',
                    msg=f'Get    '
                    f'<order:{order_id}> '
                    f'<member:{member_id}> '
                    f'<contest:{contest_id}> '
                    f'<data:{order_data}>',
                )
                try:  # 更新order
                    order_obj = Order.query.filter(
                        Order.id == order_id).with_for_update().first()
                    order_obj.member_id = member_id
                    order_obj.status = Const.OrderType.SUCCEED
                    # create member_fee_transaction
                    record = TransactionTool.get_member_trans(
                        trans_type=Const.Transaction.Member.FEE,
                        member_id=member_id,
                        order_id=order_id,
                        cash=cash,
                        ticket=ticket,
                    )
                    db.session.add(record)
                    ORMTool.commit()
                    cls._show(
                        tag='order',
                        msg=f'Update '
                        f'<order:{order_id}> '
                        f'<member:{member_id}> '
                        f'<contest:{contest_id}> '
                        f'<data:{order_data}>',
                    )
                except Exception as e:  # 有錯誤時，將contest_id push back to USED
                    DataCache.push_order_data_to_used(
                        contest_id=contest_id,
                        order_id=order_id,
                        member_id=member_id,
                        cash=cash,
                        ticket=ticket,
                    )
                    DebugTool.warning(
                        msg=f'contest id {contest_id} update error : {e}')
