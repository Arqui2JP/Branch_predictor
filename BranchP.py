
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
           invalidate,
           jalr,
           ENABLE=True,
           D_WIDTH=32,
           BLOCK_WIDTH=5,
           SET_WIDTH=9,
           WAYS=2,
           LIMIT_WIDTH=32):
    """
    The Branch Predictor module.
    :param clk:         System clock
    :param rst:         System reset
    :param pc:
    :param branch:
    :param invalidate:  Enable flush Branch Predictor
    :param jalr:
    :param Enable:      Enable Branch Predictor
    :param D_WIDTH:     Data width
    :param BLOCK_WIDTH: Address width for byte access inside a block line
    :param SET_WIDTH:   Address width for line access inside a block
    :param WAYS:        Number of ways for associative cache (Minimum: 2)
    :param LIMIT_WIDTH: Maximum width for address
    """
    if ENABLE:
        """
        PARAMETROS QUE TENDRA EL BP INTERNAMENTE. MODIFICAR

        """
        assert D_WIDTH == 32, "Error: Unsupported D_WIDTH. Supported values: {32}"
        assert BLOCK_WIDTH > 0, "Error: BLOCK_WIDTH must be a value > 0"
        assert SET_WIDTH > 0, "Error: SET_WIDTH must be a value > 0"
        assert not (WAYS & (WAYS - 1)), "Error: WAYS must be a power of 2"

        # --------------------------------------------------------------------------
        WAY_WIDTH            = BLOCK_WIDTH + SET_WIDTH  # cache mem_wbm address width
        TAG_WIDTH            = LIMIT_WIDTH - WAY_WIDTH  # tag size
        TAGMEM_WAY_WIDTH     = TAG_WIDTH + 1         # Add the valid bit
        TAGMEM_WAY_VALID     = TAGMEM_WAY_WIDTH - 1  # Valid bit index
        TAG_LRU_WIDTH        = (WAYS * (WAYS - 1)) >> 1  # (N*(N-1))/2
        # --------------------------------------------------------------------------
        """
        ESTADOS DEL BP

        """
        bp_states = enum('ST',
                         'WT',
                         'WN',
                         'SN')
        """
        INICIALIZACION DE SENALES

        """

        state              = Signal(bp_states.WT)
        n_state            = Signal(bp_states.WT)
        branch_taken       = Signal(False) #SEÑAL QUE SALE DEL EX
        condition          = Signal(False)
        prediction         = Signal(False)
        
        #SEÑALES DEL Branch Target Address Cache 
        tag                = Signal(modbv(0)[TAG_WIDTH:]) # se utilizara if_pc como etiqueta, REVISAR TAMAÑO
        adress_target      = Signal(modbv(0)[D_WIDTH:])   # direccion de salto, REVISAR TAMAÑO
        valid_bit          = Signal(False)                # bit de validez
        jump               = Signal(False)                # es un salto incondicional?, jump=1 incondicional, jump=0 condicional

        @always_comb
        def next_state_logic():
            #LOGICA DE LOS ESTADOS. COMPORTAMIENTO SIMILAR A ICACHE
            n_state.next = state
            #STRONGLY TAKEN
            if state == bp_states.ST:
                if branch_taken and (condition==prediction):
                    n_state.next = bp_states.ST
                elif branch_taken and not (condition==prediction):
                    n_state.next = bp_states.WT
            #WEAKLY TAKEN
            elif state == bp_states.WT:
                if branch_taken and (condition==prediction):
                    n_state.next = bp_states.ST
                elif branch_taken and not (condition_true==prediction):
                    n_state.next = bp_states.WN
            #WEAKLY NO TAKEN
            elif state == bp_states.WN:
                if branch_taken and (condition==prediction):
                    n_state.next = bp_states.WT
                elif branch_taken and not (condition_true==prediction):
                    n_state.next = bp_states.SN
            #STRONGLY NO TAKEN
            elif state == bp_states.SN:
                if branch_taken and (condition==prediction):
                    n_state.next = bp_states.WN
                elif branch_taken and not (condition_true==prediction):
                    n_state.next = bp_states.SN

        return instances()
    else:
        return instances()

# End:
