from myhdl import Signal
from myhdl import always
from myhdl import always_comb
from myhdl import enum
from myhdl import modbv
from myhdl import concat
from myhdl import instances
from Core.consts import Consts
from Core.instructions import Opcodes



class BranchPIO():
    #IO interface between Branch predictor, dpath and cpath

    def __init__(self):

        self.enabled            = Signal(False)         #Va al cpath
        self.valid_branch       = Signal(False)         
        self.valid_jump         = Signal(False)         
        self.valid_jalr         = Signal(False)         
        
        #Cambio senales de In-Out
        self.pc_if              = Signal(modbv(0)[32:])     
        self.pc_id_brjmp        = Signal(modbv(0)[32:])     
        self.pc_id_jalr         = Signal(modbv(0)[32:])     
        self.predict            = Signal(modbv(0)[2:0])     #Bits correspondientes a estado maquina de estado(hacia el control) Tampoco me acuerdo para que era esto :)
        self.btb_npc            = Signal(modbv(0)[32:])     #Va al dpath. Salida del btb- entrada al multiplexor
        self.branch_taken       = Signal(False)             #SE;AL QUE SALE DE ID HAY QUE CONECTARLA    
        self.current_state      = Signal(modbv(0)[2:0])
        self.change_state       = Signal(modbv(0)[2:0])
        self.fullStallReq       = Signal(False)
        self.hit                = Signal(False)
        self.stall              = Signal(False)
        self.opcode             = Signal(modbv(0)[7:])
        self.trigger            = Signal(False)
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
    SET_NUMBER = 64
    """
    STATES' SIGNALS 
    """
    state_m            = Signal(bp_states_m.IDLE)
    n_state_m          = Signal(bp_states_m.IDLE)
    read_end           = Signal(False)
    clear_done         = Signal(False)
    final_write1       = Signal(False)
    final_write2       = Signal(False)

    btb_line           = [Signal(modbv(0)[64:]) for ii in range(0, 64)]

    index_btb          = Signal(modbv(0)[6:0])
    #SE;ALES DEL Branch Target Address Cache 

    tag_pc             = Signal(modbv(0)[32:]) # se utilizara if_pc como etiqueta, REVISAR TAMAnO
    adress_target      = Signal(modbv(0)[32:])   # direccion de salto, REVISAR TAMAnO
    valid_bit          = Signal(False)                # Bit de validez. Indica si la instruccion de salto esta en el BTB. (MISS)

    miracle            = Signal(modbv(0)[1:]) 
    ####################
    current_state      = Signal(modbv(0)[2:])         # OJO- SE;AL QUE DEBE IR A CONTROL
    ####################

    #SENAL CORRESPONDIENTE A LA ALEATORIEDAD


#Cambio tama;o de registro
    #                                 
    #                         ESTRUCTURA INTERNA DEL BTB
    #
    #        VALID    UNCONDITIONAL         TAG            ADDRESS_TARGET     BTB STATE  
    #        1 bit       1 bit            30 bits              30 bits         2 bits           
    #     |          |            |                     |                 |            |   
    #     |          |            |                     |                 |            |    64 LINES
    #     |          |            |                     |                 |            | 
    #     - 63    63 - 62      62 - 61               32 - 31            2 - 1        0 -    
    #
    # --------------------------------------------------------------------------

    LINE_LENGTH         = 64
    SET_NUMBER          = 64

    random              = Signal(modbv(156)[32:])
    
    @always(clk.posedge)
    def random_change():
    #Randomness Generator 
        random.next = (random ^ (random << 1) )

    @always_comb
    def turn_trigger():
        
        if BPio.opcode == Opcodes.RV32_JAL or BPio.opcode == Opcodes.RV32_JALR or BPio.opcode == Opcodes.RV32_BRANCH:
            BPio.trigger.next = True
            tag_pc.next       = BPio.pc_if

            if BPio.opcode == Opcodes.RV32_JAL:
                BPio.valid_jump.next = True
            elif BPio.opcode == Opcodes.RV32_JALR:
                BPio.valid_jalr = True
            elif BPio.opcode == Opcodes.RV32_BRANCH:
                BPio.valid_branch.next = True


    @always_comb
    def read_process1():

        if state_m == bp_states_m.READ:

            for i in range(0, SET_NUMBER):
                if  (tag_pc[32:2] == btb_line[i][62:32] and btb_line[i][63] == True):

                    #Indice usado en proximos estados
                    index_btb.next      = modbv(i)[6:]

                    #Envio de lectura al cpath
                    BPio.btb_npc.next       = concat(modbv(btb_line[i][32:2])[30:], modbv(0)[2:])
                    BPio.current_state.next = btb_line[i][2:]


                    BPio.hit.next            = True

                if(i==SET_NUMBER-1):
                    read_end.next    = True

    @always_comb
    def read_process2():
        
        if state_m == bp_states_m.READ:
            if read_end and not BPio.hit:
                n_state_m.next        = bp_states_m.WRITE1


    #Se cambio consistente con el cambio de tamano de registro
    @always_comb
    def write_process1():
        
        if state_m == bp_states_m.WRITE1:
            
            index_r                           = random[26:20]
                        
            #btb_line[index_r][64:63].next     = Signal(True)  #Set Valid Bit
            #btb_line[index_r][61:32].next     = tag_pc[32:2]  #Store tag
            
 
            if BPio.valid_jump:
                btb_line[index_r].next        = concat(True,True,modbv(tag_pc[32:2])[30:],modbv(BPio.pc_id_brjmp[32:2])[30:],modbv(Consts.ST)[2:])
                # btb_line[index_r][63:62].next = Signal(True)              #Set Unconditional Bit
                # btb_line[index_r][2:0].next   = Consts.ST                 #As a jump it'll always be ST
                # BPio.current_state.next       = Consts.ST                 #Send our current state to Cpath
                # btb_line[index_r][32:2].next  = BPio.pc_id_brjmp[32:2]    #Store jump address in BTB

            elif BPio.valid_branch:
                btb_line[index_r].next        = concat(True,False,modbv(tag_pc[32:2])[30:],modbv(BPio.pc_id_brjmp[32:2])[30:],modbv(Consts.WN)[2:])
                #btb_line[index_r][63:62].next = Signal(False)           #Clear unconditional bit
                #btb_line[index_r][2:0].next   = Consts.WN               #It will be initialized in WN
                #BPio.current_state.next       = Consts.WN               #Send our current state to Cpath
                #btb_line[index_r][32:2].next  = BPio.pc_id_brjmp[32:2]  #Store Branch address in BTB
        
            else:   #Corresponding to JALR
                #btb_line[index_r][63:62]      = Signal(True)            #Set Unconditional bit
                #btb_line[index_r][2:0]        = Consts.ST               #As an indirect jump it'll always be taken
                #BPio.current_state.next       = Consts.ST               #Send our current state to Cpath
                #btb_line[index_r][32:2]       = BPio.pc_id_jalr[32:2]   #Store jump address in BTB  
                btb_line[index_r].next        = concat(True,True,modbv(tag_pc[32:2])[30:],modbv(BPio.pc_id_jalr[32:2])[30:],modbv(Consts.ST)[2:])

            

            final_write1.next      = True


    @always_comb
    def write_process2():

        if state_m == bp_states_m.WRITE2:

            if (BPio.current_state == Consts.ST and BPio.change_state == False):
                btb_line[index_btb][2:].next = Consts.WT
            
            if (BPio.current_state == Consts.WT and BPio.change_state == False):
                btb_line[index_btb][2:].next = Consts.WN
            if (BPio.current_state == Consts.WN and BPio.change_state == False):
                btb_line[index_btb][2:].next = Consts.SN

            if (BPio.current_state == Consts.SN and change_state == True):
                btb_line[index_btb][2:].next = Consts.WN
            if (BPio.current_state == Consts.WN and change_state == True):
                btb_line[index_btb][2:].next = Consts.WT
            if (BPio.current_state == Consts.WT and change_state == True):
                btb_line[index_btb][2:].next = Consts.ST
            


            final_write2.next = True
            


    @always_comb
    def clear_process():
        """
        Clears the whole Branch Target Predictor
        """
        if state_m == bp_states_m.CLEAR:
            
            for i in range(0,SET_NUMBER):
                btb_line[i].next  = 0
        
            clear_done.next = Signal(True)
            index_btb.next  = modbv(0)[6:]

    @always_comb
    def  stallReq():
        
        if state_m == bp_states_m.CLEAR:
            BPio.fullStallReq.next = True

        else:
            BPio.fullStallReq.next = False
    
    """
    BTB STATES DRIVING
    """

    @always(clk.posedge)
    def update_state():
        if rst:
            state_m.next = bp_states_m.CLEAR 
        else:
            state_m.next = n_state_m
    

    @always_comb
    def next_state_logic_m(): #MAQUINA DE ESTADOS
        

        n_state_m.next = state_m
        
        if rst:
            n_state_m.next = bp_states_m.CLEAR

        
        else:   

            if state_m == bp_states_m.CLEAR:

                if clear_done:
                    n_state_m.next = bp_states_m.IDLE
                else:
                    n_state_m.next = bp_states_m.CLEAR

            elif state_m == bp_states_m.IDLE and not BPio.stall :

                if BPio.trigger:
                    n_state_m.next = bp_states_m.READ
                elif rst == 1:
                    n_state_m.next = bp_states_m.CLEAR

            elif state_m == bp_states_m.READ and not BPio.stall:

                if BPio.hit == True:
                    n_state_m.next = bp_states_m.WRITE2
                else:
                    n_state_m.next = bp_states_m.WRITE1

            elif state_m == bp_states_m.WRITE1 and not BPio.stall:
                if final_write1:
                    n_state_m.next = bp_states_m.IDLE
            
            elif state_m == bp_states_m.WRITE2 and not BPio.stall:
                if final_write2:
                    n_state_m.next = bp_states_m.IDLE
    

    @always_comb
    def clear_triggers():
        
        if not (state_m == bp_states_m.CLEAR):
            clear_done.next   = Signal(False)

        if not (state_m == bp_states_m.READ):
            BPio.hit.next     = Signal(False)
            read_end.next     = Signal(False)
            BPio.trigger.next = Signal(False)


        if not (state_m == bp_states_m.WRITE1):
            final_write1.next      = Signal(False)
            BPio.valid_jump.next   = Signal(False)
            BPio.valid_jalr.next   = Signal(False)
            BPio.valid_branch.next = Signal(False)
        
        if not (state_m == bp_states_m.WRITE2):
            final_write2.next      = Signal(False)
            BPio.valid_jump.next   = Signal(False)
            BPio.valid_jalr.next   = Signal(False)
            BPio.valid_branch.next = Signal(False)

    return instances()

# End:
