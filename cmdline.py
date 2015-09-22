import argparse, logging

class ParseLoglevel(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        # 'choices' dictionary provided as argument to add_argument()
        # is used both in validation of string values and conversion
        # to loglevel constant
        if len(kwargs['choices']) is 0:
            raise ValueError("dict with valid logging choices must be provided")
        self.loglevels = kwargs['choices']
        super(ParseLoglevel, self).__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        loglevel = self.parse_loglevel(values, self.loglevels)
        setattr(namespace, self.dest, loglevel)
    def parse_loglevel(self, loglevel_string, loglevels):
        try:
            return loglevels[loglevel_string]
        except:
            msg = '{} is not a supported loglevel'.format(loglevel_string)
            raise argparse.ArgumentTypeError(msg)

    loglevels = { 'debug' : logging.DEBUG,
                  'info' : logging.INFO,
                  'warn' : logging.WARNING }

class Command:
    def __init__(self,helpstring=''):

        self.__parser = argparse.ArgumentParser(description=helpstring)
        self.__parser.add_argument('-l','--loglevel', help='log message verbosity [default: \'warn\']',
                default=logging.WARNING, choices=ParseLoglevel.loglevels, action=ParseLoglevel)

    def add_argument(self, *args, **kwargs):
        self.__parser.add_argument(*args, **kwargs)

    def parse_args(self, *args, **kwargs):
        self.args = self.__parser.parse_args(*args, **kwargs)

        self.__log = logging.getLogger(__name__)
        self.__log.setLevel(self.args.loglevel)
        self.__log.addHandler(logging.StreamHandler())

        self.debug('[HOST:%s] parsed command line arguments %s', self.__class__.__name__, self.args)

    def warn(self, *args, **kwargs):
        self.__log.warn(*args, **kwargs)

    def info(self, *args, **kwargs):
        self.__log.info(*args, **kwargs)

    def debug(self, *args, **kwargs):
        self.__log.debug(*args, **kwargs)

    def __get_log(self):
        return self.__log

    log = property(__get_log)
