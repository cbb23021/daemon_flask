from core.join_handler import JoinHandler
from common.utils.debugtool import DebugTool

DebugTool.start_logging(__file__)

if __name__ == '__main__':
    JoinHandler.exec()
