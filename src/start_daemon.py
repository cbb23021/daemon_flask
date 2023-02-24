from core.join_contest_handler import JoinContestHandler
from general.debugtool import DebugTool

DebugTool.start_logging(__file__)

if __name__ == '__main__':
    JoinContestHandler.exec()
