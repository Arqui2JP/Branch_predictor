from myhdl import Signal
from myhdl import always
from myhdl import always_comb
from myhdl import enum
from myhdl import modbv
from myhdl import concat
from myhdl import instances



class BranchPIO()
    #IO interface between Branch predictor, dpath and cpath

    def __init__(self):
        self.enable             = Signal(False)         #Va al cpath
        self.valid_branch       = Signal(False)         #viene del cpath
        self.valid_jump         = Signal(False)         #viene del cpath
        #Cambio señales de io
        self.pc_if              = Signal(modbv(0)[32:])     #viene del dpath
        self.pc_id              = Signal(modbv(0)[32:])     #viene del dpath
        self.pc_id_brjmp        = Signal(modbv(0)[32:])     #viene del dpath
        self.pc_id_jalr         = Signal(modbv(0)[32:])
        self.predict            = Signal(modbv(0)[2:0]) #Bits correspondientes a estado maquina de estado(hacia el control) Tampoco me acuerdo para que era esto :)
        self.btb_npc            = Signal(modbv(0)[32:])     #Va al dpath. Salida del btb- entrada al multiplexor
        self.branch_taken       = Signal(False)             #SEÑAL QUE SALE DE ID HAY QUE CONECTARLA    
        self.current_state      = Signal(modbv(0)[1:0])
        self.change_state       = Signal(modbv(0)[1:0])
        self.fullStallReq       = Signal(False)
        self.hit                = Signal(False)
        #Fin cambio

def BranchP(clk,
           rst,
           BPio):
    """
    The Branch Predictor module.
    :param clk:         System clock
    :param rst:         System reset
    :param BPio:        IO bundle. Interface with the dpath and cpath modules
    """
    
    """
    ESTADOS DEL BP_MACHINE
    """
    bp_states_m = enum('IDLE',
                       'READ',
                       'WRITE1',
                       'WRITE2',
                       'CLEAR')
    """
    INICIALIZACION DE SENALES
    """

    state_m            = Signal(bp_states_m.IDLE)
    n_state_m          = Signal(bp_states_m.IDLE)

    condition          = Signal(False)
    prediction         = Signal(False)
    final_write1       = Signal(False)
    final_write2       = Signal(False)
    final_flush        = Signal(False)
    index_btb          = Signal(modbv(0)[6:0])
    #SEÑALES DEL Branch Target Address Cache 
    tag_pc             = Signal(modbv(0)[TAG_WIDTH:]) # se utilizara if_pc como etiqueta, REVISAR TAMAÑO
    adress_target      = Signal(modbv(0)[D_WIDTH:])   # direccion de salto, REVISAR TAMAÑO
    valid_bit          = Signal(False)                # Bit de validez. Indica si la instruccion de salto esta en el BTB. (MISS)
    clear_done         = Signal(False)
    ####################
    current_state      = Signal(modbv(0)[2:])         # OJO- SE;AL QUE DEBE IR A CONTROL
    ####################

    #SENAL CORRESPONDIENTE A LA ALEATORIEDAD
    random              = Signal(modbv(4, min=0, max = SET_NUMBER)) 

#Cambio tama;o de registro
    #                                 
    #                         ESTRUCTURA INTERNA DEL BTB
    #
    #        VALID    INCONDITIONAL         TAG            ADDRESS_TARGET     BTB STATE  
    #        1 bit       1 bit            30 bits              30 bits         2 bits           
    #     |          |            |                     |                 |            |   
    #     |          |            |                     |                 |            |    64 LINES
    #     |          |            |                     |                 |            | 
    #     - 63    63 - 62      62 - 61               32 - 31            2 - 1        0 -    
    #
    # --------------------------------------------------------------------------

    LINE_LENGTH         = 64
    SET_NUMBER          = 64

    @always(clk.posedge)
    def random_change():
    #Randomness Generator 
        random.next = random ^ (random << 2)
#Fin de cambio

    @always(clk.posedge)
    def assignments():
    #Inicializacion del BTB
        if rst:
            index_btb.next      = modbv(0)[6:]
            for i in range(0,SET_NUMBER):
                btb_line[i].next = Signal(modbv(0)[LINE_LENGTH:0])

    @always_comb
    def read_process():
        if state_m == bp_states_m.READ:
            for i in range(0, SET_NUMBER):
                if  (tag_pc[32:2] == btb_line[i][61:32]):

                    valid_bit.next      = True
                    index_btb.next      = modbv(i)[6:]
            
                    #Envio de lectura al cpath
                    BPio.btb_npc.next       = concat(btb_line[i][31:2], Signal(modbv(0)[1:]))
                    BPio.current_state.next = btb_line[i][1:]

                    BPio.hit.next            = True
                    state_m.next             = bp_states_m.WRITE2

                if (i==SET_NUMBER) and not BPio.hit:
                    state_m.next        = bp_states_m.WRITE1
 
    
    @always_comb
    def  stallReq:
        if state_m == bp_states_m.CLEAR:
            BPio.fullStallReq = True
        else:
            BPio.fullStallReq = False

    @always(clk.posedge)
    def update_state():
        if rst:
            state_m.next = bp_states_m.CLEAR 
        else:
            state_m.next = n_state_m

#Se cambio consistente con el cambio de tamaño de registro
    @always_comb
    def write_process1():
        if state_m == bp_states_m.WRITE1:
            index_r                           = random.unsigned
            index_btb.next                    = modbv(index_r)[6:]
            btb_line[index_r][63].next        = True
            btb_line[index_r][61:32].next     = tag_pc[32:2]
            btb_line[index_r][31:2].next      = pc_id_brjmp

            if BPio.valid_jump:
                btb_line[index_r][62].next    = True
                btb_line[index_r][1:0].next   = Const.ST      #Primer guardado se toma como ST, si es un jump
                #Envio al cpath del estado base (jump=ST)
                BPio.current_state.next       = Const.ST      #Lo que se envia al cpath
            if BPio.valid_branch:
                btb_line[index_r][62].next    = False
                btb_line[index_r][1:0].next   = Const.WN      #Primer guardado se toma como WN, si es un branch
                #Envio al cpath del estado base
                BPio.current_state.next       = Const.WN      #Lo que se envia al cpath

            final_write1.next                  = True

    @always_comb
    def write_process2():
        if state_m == bp_states_m.WRITE2 and (BPio.valid_jump or BPio.valid_branch):
            BPio.hit.next          = False
            BPio.branch_taken      = False

            if (BPio.current_state == Const.ST and BPio.change_state == False)
                btb_line[index_btb][1:].next = Const.WT
            if (BPio.current_state == Const.WT and BPio.change_state == False)
                btb_line[index_btb][1:].next = Const.WN
            if (BPio.current_state == Const.WN and BPio.change_state == False)
                btb_line[index_btb][1:].next = Const.SN

            if (BPio.current_state == Const.SN and change_state == True)
                btb_line[index_btb][1:].next = Const.WN
            if (BPio.current_state == Const.WN and change_state == True)
                btb_line[index_btb][1:].next = Const.WT
            if (BPio.current_state == Const.WT and change_state == True)
                btb_line[index_btb][1:].next = Const.ST

            if (BPio.current_state == Const.ST and change_state == True) or (BPio.current_state == Const.SN and change_state == False)
                btb_line[index_btb][1:].next = btb_line[index_btb][1:]

            final_write2.next = True
            

    @always_comb
    def clear_process():
        if state_m == bp_states_m.CLEAR:
            for i in range(0,SET_NUMBER):
                btb_line[i].next  = 0
        clear_done.next = True

    @always_comb
    def next_state_logic_m(): #MAQUINA DE ESTADOS
        n_state_m.next = state_m
        
        if state_m == bp_states_m.CLEAR:
            if clear_done == True:
                n_state_m.next = bp_states_m.IDLE
                clear_done.next = False
            else:
                n_state_m.next = bp_states_m.CLEAR
        elif state_m == bp_states_m.IDLE:
            if valid_branch or valid_jump:
                n_state_m.next = bp_states_m.READ
            elif rst == 1:
                n_state_m.next = bp_states_m.CLEAR
        elif state_m == bp_states_m.WRITE1:
            if final_write1:
                n_state_m.next = bp_states_m.WRITE2
                final_write1   = False
        elif state_m == bp_states_m.WRITE2:
            if final_write2:
                n_state_m.next = bp_states_m.IDLE
                final_write2   = False

    return instances()

# End:
