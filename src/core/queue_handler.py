import json
from datetime import datetime, timedelta

from colorama import Fore

from app import db
from common.const import Const
from common.models import LottoOrder
from common.utils.data_cache import DataCache
from common.utils.debugtool import DebugTool
from common.utils.order_tool import OrderTool
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
    def create_empty_orders(cls, draw):
        """ 建立空注單 並將order_id存入<draw_id>-WAIT中 """
        obj_list = list()
        size = draw.size
        for _ in range(size):
            order = OrderTool.create_lotto_order(type_=Const.Order.Type.LOTTO)
            obj_list.append(order)
        db.session.bulk_save_objects(obj_list, return_defaults=True)
        db.session.flush()
        db.session.commit()
        obj_ids_list = [obj.id for obj in obj_list]

        # 檢查空注單是否全部新增完成，若否 則確認miss幾張後補建立
        while True:
            if len(obj_ids_list) == size:
                break
            missing_draw_size = size - len(obj_ids_list)
            missing_obj_list = list()
            for _ in range(missing_draw_size):
                order = OrderTool.create_lotto_order(
                    type_=Const.Order.Type.LOTTO)
                missing_obj_list.append(order)
            db.session.bulk_save_objects(missing_obj_list,
                                         return_defaults=True)
            db.session.flush()
            for obj in missing_obj_list:
                obj_ids_list.append(obj)
        db.session.commit()

        DataCache.push_order_data_to_wait(draw_id=draw.id, value=obj_ids_list)
        cls._show(
            tag='order',
            msg=f'Init empty order done. <draw:{draw.id}> by nums: {len(obj_ids_list)}'
        )

    @classmethod
    def used_monitor(cls, draw_id, open_dt):
        """
            pop data from <draw_id>-WAIT
            format => order_id:member_id:cash:ticket:join_dt:remar
        """
        while True:
            # cancel part
            # cancel_draw_ids = DataCache.get_cancel_draw_signal()
            # if str(draw_id) in cancel_draw_ids:
            #     cls._show(tag='log',
            #               color=Fore.YELLOW,
            #               msg=f'>>>>> Cancel <draw:{draw_id}>')
            #     DataCache.del_cancel_draw_signal(draw_id=draw_id)
            #     return True

            if datetime.now() > open_dt + timedelta(hours=5):
                cls._show(tag='log',
                          color=Fore.YELLOW,
                          msg=f'>>>>> Stop Listen 5hr <draw:{draw_id}>')
                return True

            order_data = DataCache.get_used_order_data(draw_id=draw_id)
            if order_data:
                order_id, member_id, cash, ticket, a, b, c, d, e, f, g, join_dt, remark = order_data[
                    1].split(':')
                order_id = int(order_id)
                member_id = int(member_id)
                cash = int(cash)
                ticket = int(ticket)
                a = int(a)
                b = int(b)
                c = int(c)
                d = int(d)
                e = int(e)
                f = int(f)
                g = int(g)
                join_dt = datetime.strptime(join_dt, "%Y-%m-%dT%H-%M-%S")
                remark = str(remark)

                cls._show(
                    tag='order',
                    msg=f'Get    '
                    f'<order:{order_id}> '
                    f'<member:{member_id}> '
                    f'<draw:{draw_id}> '
                    f'<data:{order_data}>',
                )
                try:  # 更新order
                    order_obj = LottoOrder.query.filter(
                        LottoOrder.id == order_id).with_for_update().first()
                    order_obj.member_id = member_id
                    order_obj.number = {
                        'numbers': json.dumps([a, b, c, d, e, f, g])
                    }

                    # create member_fee_transaction
                    record = TransactionTool.get_member_trans(
                        trans_type=Const.Transaction.Type.LOTTO_FEE,
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
                        f'<draw:{draw_id}> '
                        f'<data:{order_data}>',
                    )
                except Exception as e:  # 有錯誤時，將draw_id push back to USED
                    DataCache.push_order_data_to_used(
                        draw_id=draw_id,
                        order_id=order_id,
                        member_id=member_id,
                        cash=cash,
                        ticket=ticket,
                        a=a,
                        b=b,
                        c=c,
                        d=d,
                        e=e,
                        f=f,
                        g=g,
                        join_dt=join_dt,
                        remark=remark,
                    )
                    DebugTool.warning(
                        msg=f'draw id {draw_id} update error : {e}')
