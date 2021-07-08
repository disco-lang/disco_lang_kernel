from ipykernel.kernelbase import Kernel
from pexpect import replwrap, EOF
import pexpect

from subprocess import check_output
import os.path

import re
import signal

__version__ = '0.1'

class IREPLWrapper(replwrap.REPLWrapper):
    """A subclass of REPLWrapper that gives incremental output
    specifically for disco_lang_kernel.

    The parameters are the same as for REPLWrapper, except for one
    extra parameter:

    :param line_output_callback: a callback method to receive each batch
      of incremental output. It takes one string parameter.
    """
    def __init__(self, cmd_or_spawn, orig_prompt, prompt_change,
                 extra_init_cmd=None, line_output_callback=None):
        self.line_output_callback = line_output_callback
        replwrap.REPLWrapper.__init__(self, cmd_or_spawn, orig_prompt,
                                      prompt_change, extra_init_cmd=extra_init_cmd)

    def _expect_prompt(self, timeout=-1):
        if timeout == None:
            # "None" means we are executing code from a Jupyter cell by way of the run_command
            # in the do_execute() code below, so do incremental output.
            while True:
                pos = self.child.expect_exact([self.prompt, self.continuation_prompt, u'\r\n'],
                                              timeout=None)
                if pos == 2:
                    # End of line received
                    self.line_output_callback(self.child.before + '\n')
                else:
                    if len(self.child.before) != 0:
                        # prompt received, but partial line precedes it
                        self.line_output_callback(self.child.before)
                    break
        else:
            # Otherwise, use existing non-incremental code
            pos = replwrap.REPLWrapper._expect_prompt(self, timeout=timeout)

        # Prompt received, so return normally
        return pos

class DiscoKernel(Kernel):
    implementation = 'disco_lang_kernel'
    implementation_version = __version__

    @property
    def language_version(self):
        return "0.1"

    _banner = None

    @property
    def banner(self):
        if self._banner is None:
            self._banner = u'Disco 0.1'
        return self._banner

    language_info = {'name': 'Disco',
                     'codemirror_mode': 'shell',
                     'mimetype': 'text/x-disco-lang',
                     'file_extension': '.disco'}

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self._start_disco()

    def _start_disco(self):
        # Signal handlers are inherited by forked processes, and we can't easily
        # reset it from the subprocess. Since kernelapp ignores SIGINT except in
        # message handlers, we need to temporarily reset the SIGINT handler here
        # so that disco and its children are interruptible.
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            child = pexpect.spawn("disco", [], echo=False,
                                  encoding='utf-8', codec_errors='replace')
            
            self.discowrapper = IREPLWrapper(child, u'Disco>', None,
                    line_output_callback=self.process_output)
        finally:
            signal.signal(signal.SIGINT, sig)

    def process_output(self, output):
        if not self.silent:
            # Send standard output
            stream_content = {'name': 'stdout', 'text': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        self.silent = silent
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        interrupted = False
        try:
            # Note: timeout=None tells IREPLWrapper to do incremental
            # output.  Also note that the return value from
            # run_command is not needed, because the output was
            # already sent by IREPLWrapper.
            ls = code.rstrip().splitlines()
            if len(ls) == 1:
                self.discowrapper.run_command(ls[0], timeout=None)
            else:
                self.discowrapper.run_command(":{")
                for l in ls:
                    self.discowrapper.run_command(l.rstrip(), timeout=None)
                self.discowrapper.run_command(":}")
        except KeyboardInterrupt:
            self.discowrapper.child.sendintr()
            interrupted = True
            self.discowrapper._expect_prompt()
            output = self.discowrapper.child.before
            self.process_output(output)
        except EOF:
            output = self.discowrapper.child.before + 'Restarting Disco'
            self._start_disco()
            self.process_output(output)

        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}

        # TODO: detect an error result and handle that differently.
        return {'status': 'ok', 'execution_count': self.execution_count,
                'payload': [], 'user_expressions': {}}

    def do_complete(self, code, cursor_pos):
        # TODO: add completion when disco has that feature.
        code = code[:cursor_pos]
        default = {'matches': [], 'cursor_start': 0,
                   'cursor_end': cursor_pos, 'metadata': dict(),
                   'status': 'ok'}
        return default