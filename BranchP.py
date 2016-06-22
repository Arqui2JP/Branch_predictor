
from myhdl import Signal
from myhdl import always
from myhdl import always_comb
from myhdl import enum
from myhdl import modbv
from myhdl import concat
from myhdl import instances

def BranchP(clk,
           rst,
           pc,
           branch,
           jalr,
           ENABLE=True):
    """
    The Branch Predictor module.

    :param clk:         System clock
    :param rst:         System reset
    :param pc:
    :param branch:
    :param jalr:
    :param Enable:	Enable Branch Predictor
    """
    if ENABLE:
	
    	return instances()
    else:
    	return instances()
# End:
