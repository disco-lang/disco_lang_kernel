from ipykernel.kernelapp import IPKernelApp
from .kernel import DiscoKernel
IPKernelApp.launch_instance(kernel_class=DiscoKernel)
