class MOS(DataClassification):
    name="MOS"
    # this a description of the intent of the classification
    # to what does the classification apply?
    usage = '''
        Applies to all MOS data which conformed to the required MOS 
        
        '''
    requirement= ISCLASS("GMOS_MOS")

newtypes.append( MOS())
