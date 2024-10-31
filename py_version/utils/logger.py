import logging
import colorlog

class Logger(object):

    @staticmethod
    def get_logger(name):
        logger = logging.getLogger(name)
        for handler in logger.handlers[:]:  # 使用 logger.handlers[:] 创建一个副本，以避免修改时出现问题
            logger.removeHandler(handler)  # 从 logger 中移除该处理器
            handler.close()  # 关闭处理器，释放资源

        # 创建处理器：sh为控制台处理器，fh为文件处理器
        sh = logging.StreamHandler()
        # 创建格式器,并将sh，fh设置对应的格式
        formater = colorlog.ColoredFormatter(fmt="%(white)s %(asctime)s %(filename)s %(log_color)s %(levelname)s %(reset)s %(blue)s %(message)s",
                                     datefmt="%Y/%m/%d %X",
                                     reset=True,
                                     log_colors={
                                         'DEBUG': 'cyan',
                                         'INFO': 'green',
                                         'WARNING': 'yellow',
                                         'ERROR': 'red',
                                         'CRITICAL': 'red,bg_white',
                                     }
                                     )
        sh.setFormatter(formater)
        logger.addHandler(sh)
        logger.setLevel(logging.DEBUG)
        return logger
