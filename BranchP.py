from myhdl import Signal
from myhdl import always
from myhdl import always_comb
from myhdl import enum
from myhdl import modbv
from myhdl import concat
from myhdl import instances
##Entradas
#id_pc 


class BranchPIO()
    #IO interface between Branch predictor, dpath and cpath

    def __init__(self):
        self.enable             = Signal(False)         #Va al cpath
        self.valid_branch       = Signal(False)         #viene del cpath
        self.valid_jump         = Signal(False)         #viene del cpath
        #self.pc        =   #Creo que es innecesaria 
        #Cambio señales de io
        self.pc_if              = Signal(modbv(0)[32:])     #viene del dpath
        self.pc_id              = Signal(modbv(0)[32:])     #viene del dpath
        self.pc_id_brjmp        = Signal(modbv(0)[32:])     #viene del dpath
        self.pc_id_jalr         = Signal(modbv(0)[32:])
        #self           = if_instruction #dpath         #No se para que era esto
        self.predict            = Signal(modbv(0)[2:0]) #Bits correspondientes a estado maquina de estado(hacia el control) Tampoco me acuerdo para que era esto :)
        self.btb_npc            = Signal(modbv(0)[32:])     #Va al dpath. Salida del btb- entrada al multiplexor
        self.branch_taken       = Signal(False)             #SEÑAL QUE SALE DE ID HAY QUE CONECTARLA    
        self.current_state      = Signal(modbv(0)[1:0])
        self.change_state       = Signal(modbv(0)[2:0])
        self.fullStallReq 		= Signal(False)

        #Fin cambio

def BranchP(clk,
           rst,
           BPio,       #se borro la señal pc porque ya se incluye en BranchPIO
           branch,
           invalidate,
           jalr,
           ENABLE): #SOPHIA REVISA ESTOOOO! ctrlIO va? Agregamos una señal que sale del cpath (señal:current_state)!!!
    """
    The Branch Predictor module.
    :param clk:         System clock
    :param rst:         System reset
    :param BPio:        IO bundle. Interface with the branchp module
    :param pc:
    :param branch:
    :param invalidate:  Enable flush Branch Predictor
    :param jalr:
    :param Enable:      Enable Branch Predictor
    """
    

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
                       'WRITE1',
                       'WRITE2',
                       'CLEAR')
    """
    INICIALIZACION DE SENALES
    """

    state_p            = Signal(bp_states_p.WN)
    n_state_p          = Signal(bp_states_p.WN)

    state_m            = Signal(bp_states_m.IDLE)
    n_state_m          = Signal(bp_states_m.IDLE)

    


    condition          = Signal(False)
    prediction         = Signal(False)
    final_write        = Signal(False)
    final_flush        = Signal(False)
    hit                = Signal(False)
    index_btb          = Signal(modbv(0)[6:0])
    #SEÑALES DEL Branch Target Address Cache 
    tag_pc             = Signal(modbv(0)[TAG_WIDTH:]) # se utilizara if_pc como etiqueta, REVISAR TAMAÑO
    adress_target      = Signal(modbv(0)[D_WIDTH:])   # direccion de salto, REVISAR TAMAÑO
    valid_bit          = Signal(False)                # Bit de validez. Indica si la instruccion de salto esta en el BTB. (MISS)
    clear_done		   = Signal(False)
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
    #     |          |            |                     |                 |            | 
    #     |          |            |                     |                 |            | 
    #     - 63    63 - 62      62 - 61               32 - 31            2 - 1        0 -    
    #
    # --------------------------------------------------------------------------

    LINE_LENGTH         = 64
    SET_NUMBER          = 64
    ADDRESS_WIDTH       = 32
    WAY_WIDTH           = 2 + 6                     # BLOCK_WIDTH + SET_WIDTH (2+6)
    D_WIDTH             = 32
    TAG_WIDTH           = 26                        # Tamaño del TAG, un poco menor al tamaño total del pc   
    WAYS                = 2

    @always(clk.posedge)
    def random_change():
    #Randomness Generator 
        random.next = random ^ (random << 2)
#Fin de cambio

    @always(clk.posedge)
    def assignments():
    #Inicializacion del BTB
        if rst:
            for i in range(0,SET_NUMBER):
                btb_line[i].next = Signal(modbv(0)[LINE_LENGTH:0])

    @always_comb
    def miss_check():
        if state_m == bp_states_m.READ:
            for i in range(0, SET_NUMBER):
                if  (tag_pc[32:2] == btb_line[i][61:32]):

                    valid_bit.next      = True
                    index_btb.next      = modbv(i)[6:]
            
                    #LECTURA INMEDIATA
                    BPio.btb_npc.next       = concat(btb_line[i][31:2], Signal(modbv(0)[1:]))
                    BPio.current_state.next = btb_line[i][1:]

                    hit.next            = True
                    state_m.next        = bp_states_m.WRITE2

                if (i==SET_NUMBER) and not hit:
                    state_m.next        = bp_states_m.WRITE1
                    hit.next     = False

    #que onda con esto?
    @always(clk.posedge)
    def btb():
        if rst:
        
        else:
    
    @always_comb
    def  stallReq:
    	if state_m == bp_states_m.CLEAR:
    		BPio.fullStallReq = True
    	else:
    		BPio.fullStallReq = False

    @always(clk.posedge)
    def update_state():
        if rst:
            state_p.next = bp_states_p.WN 
            state_m.next = bp_states_m.CLEAR 
        else:
            state_p.next = n_state_p
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

            if bp.valid_jump:
                btb_line[index_r][62].next    = True
            if bp.valid_branch:
                btb_line[index_r][62].next    = False

            if bp_states_p == bp_states_p.ST:
                btb_line[index_r][1:0].next   = 11
                current_state.next            = 11
            if bp_states_p == bp_states_p.WT:
                btb_line[index_r][1:0].next   = 10
                current_state.next            = 10
            if bp_states_p == bp_states_p.WN:
                btb_line[index_r][1:0].next   = 01
                current_state.next            = 01
            if bp_states_p == bp_states_p.SN:
                btb_line[index_r][1:0].next   = 00
                current_state.next            = 00

            final_write.next                  = True
            #blablablablabla

        if BPio.branch_taken == True:
            BPio.branch_taken = False

                #ACTUALIZAR PREDICTOR
        else:

                #Flush etapada if. actualizar predictor. busqueda de instruccion
    @always_comb
    def write_process2():

    	if state_m == bp_states_m.WRITE2:

            if bp_states_p == bp_states_p.ST:
                btb_line[indexto][1:0].next   = 11
                current_state.next            = 11
            if bp_states_p == bp_states_p.WT:
                btb_line[indexto][1:0].next   = 10
                current_state.next            = 10
            if bp_states_p == bp_states_p.WN:
                btb_line[indexto][1:0].next   = 01
                current_state.next            = 01
            if bp_states_p == bp_states_p.SN:
                btb_line[indexto][1:0].next   = 00
                current_state.next            = 00

            final_write.next                  = True
            #blablablablabla

        if BPio.branch_taken == True:
            BPio.branch_taken = False

                #ACTUALIZAR PREDICTOR
        else:

                #Flush etapada if. actualizar predictor. busqueda de instruccion




    @always_comb
    def clear_process():
    	if state_m == bp_states_m.CLEAR:
    		for i in range(0,SET_NUMBER):
    			btb_line[i].next  = 0
    	clear_done.next = True




#Fin de cambio


    @always_comb
    def next_state_logic_p(): #LOGICA DE LOS ESTADOS. COMPORTAMIENTO SIMILAR A ICACHE
        n_state_p.next = state_p
        #STRONGLY TAKEN
        if state_p == bp_states_p.ST:
            if branch_taken and current_state:
                n_state_p.next = bp_states_p.ST

            elif branch_taken and not current_state:
                n_state_p.next = bp_states_p.WT
        #WEAKLY TAKEN
        elif state_p == bp_states_p.WT:
            if branch_taken and current_state:
                n_state_p.next = bp_states_p.ST
            elif branch_taken and not current_state:
                n_state_p.next = bp_states_p.WN
        #WEAKLY NO TAKEN
        elif state_p == bp_states_p.WN:
            if branch_taken and current_state:
                n_state_p.next = bp_states_p.WT
            elif branch_taken and not current_state:
                n_state_p.next = bp_states_p.SN
        #STRONGLY NO TAKEN
        elif state_p == bp_states_p.SN:
            if branch_taken and current_state:
                n_state_p.next = bp_states_p.WN
            elif branch_taken and not current_state:
                n_state_p.next = bp_states_p.SN

    @always_comb
    def next_state_logic_m(): #MAQUINA DE ESTADOS
        n_state_m.next = state_m
        
        if state_m == bp_states_m.CLEAR:
        	if clear_done == 1:
        		n_state_m.next = bp_states_m.IDLE
        		clear_done.next = 0
        	else:
        		n_state_m.next = bp_states_m.CLEAR
        if state_m == bp_states_m.IDLE:
            if valid_branch or valid_jump:
                n_state_m.next = bp_states_m.READ
            elif rst == 1:
            	n_state_m.next = bp_states_m.CLEAR
        elif state_m == bp_states_m.WRITE1:
            if final_write:
                n_state_m.next = bp_states_m.IDLE
                final_write    = False
        elif state_m == bp_states_m.READ:
            if 	rst == 1:
            	n_state_m.next = bp_states_m.CLEAR
            elif valid_bit:
                # not valid_bit: refill line
                n_state_m.next = bp_states_m.IDLE
            else:
                n_state_m.next = bp_states_m.WRITE

    
    return instances()

# End:
