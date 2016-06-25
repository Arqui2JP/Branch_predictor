from myhdl import Signal
from myhdl import always
from myhdl import always_comb
from myhdl import enum
from myhdl import modbv
from myhdl import concat
from myhdl import instances
#AGREGAR SEÑAL DEL CPATH

def BranchP(clk,
           rst,
           BranchPIO,
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
    :param BranchPIO:   IO bundle. Interface with the branchp module
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
        ESTADOS DEL BP_PREDICTOR
        """
        bp_states_p = enum('ST',
                           'WT',
                           'WN',
                           'SN')

        """
        ESTADOS DEL BP_MACHINE
        """
        bp_states_m = enum('IDLE',
                           'READ',
                           'WRITE',
                           'FLUSH',
                           'FLUSH_LAST')


        """
        INICIALIZACION DE SENALES
        """

        state_p            = Signal(bp_states_p.WN)
        n_state_p          = Signal(bp_states_p.WN)

        state_m            = Signal(bp_states_m.IDLE)
        n_state_m          = Signal(bp_states_m.IDLE)

        branch_taken       = Signal(False) #SEÑAL QUE SALE DEL EX
        condition          = Signal(False)
        prediction         = Signal(False)
        final_write        = Signal(False)
        final_flush        = Signal(False)


        #SEÑALES DEL Branch Target Address Cache 
        tag                = Signal(modbv(0)[TAG_WIDTH:]) # se utilizara if_pc como etiqueta, REVISAR TAMAÑO
        adress_target      = Signal(modbv(0)[D_WIDTH:])   # direccion de salto, REVISAR TAMAÑO
        valid_bit          = Signal(False)                # Bit de validez. Indica si la instruccion de salto esta en el BTB. (MISS)
        valid_branch       = Signal(False)                # Indica si la instruccion es de tipo branch
        valid_jump         = Signal(False)                # es un salto incondicional?, jump=1 incondicional, jump=0 condicional


        #       ESTRUCTURA INTERNA DEL BTB
        #
        #
        #        TAG         ADRESS_TARGET      
        #
        #      32 bits         32 bits
        #
        #
        #
        #
        #


        @always_comb
        def verify_instruction():
            



        @always_comb
        def next_state_logic_p(): #LOGICA DE LOS ESTADOS. COMPORTAMIENTO SIMILAR A ICACHE
            n_state_p.next = state_p
            #STRONGLY TAKEN
            if state_p == bp_states_p.ST:
                if branch_taken and (condition==prediction):
                    n_state_p.next = bp_states_p.ST
                elif branch_taken and not (condition==prediction):
                    n_state_p.next = bp_states_p.WT
            #WEAKLY TAKEN
            elif state_p == bp_states_p.WT:
                if branch_taken and (condition==prediction):
                    n_state_p.next = bp_states_p.ST
                elif branch_taken and not (condition==prediction):
                    n_state_p.next = bp_states_p.WN
            #WEAKLY NO TAKEN
            elif state_p == bp_states_p.WN:
                if branch_taken and (condition==prediction):
                    n_state_p.next = bp_states_p.WT
                elif branch_taken and not (condition==prediction):
                    n_state_p.next = bp_states_p.SN
            #STRONGLY NO TAKEN
            elif state_p == bp_states_p.SN:
                if branch_taken and (condition==prediction):
                    n_state_p.next = bp_states_p.WN
                elif branch_taken and not (condition==prediction):
                    n_state_p.next = bp_states_p.SN

        @always_comb
        def next_state_logic_m(): #MAQUINA DE ESTADOS
            n_state_m.next = state_m
            if state_m == bp_states_m.IDLE:
                if not valid_bit and valid_branch:
                    n_state_m.next = bp_states_m.WRITE
                elif valid_bit and valid_branch:
                    n_state_m.next = bp_states_m.READ
            elif state_m == bp_states_m.WRITE:
                if final_write:
                    n_state_m.next = bp_states_m.IDLE
            elif state_m == bp_states_m.READ:
                if valid_bit:
                    # not valid_bit: refill line
                    n_state_m.next = bp_states_m.IDLE
                else:
                    n_state_m.next = bp_states_m.WRITE
            elif state_m == bp_states_m.FLUSH:
                if final_flush
                    n_state_m.next = bp_states_m.FLUSH_LAST
                else:
                    n_state_m.next = bp_states_m.FLUSH
            elif state_m == bp_states_m.FLUSH_LAST:
                #Ultimo FLUSH
                n_state_m.next = bp_states_m.IDLE

        @always(clk.posedge)
        def update_state_p():
            if rst:
                state_p.next = bp_states_p.WN #REVISAR SI TIENE QUE SER FLUSH
            else:
                state_p.next = n_state_p

        return instances()
    else:
        return instances()

# End:
