#Author: Kyle Mede, Aug 2010
# This module provides functions that perform numpy operations on astrodata
# objects

import os

import pyfits as pf
import numpy as np
from copy import deepcopy
import astrodata
from astrodata.AstroData import AstroData
from astrodata.adutils import varutil
from astrodata.Errors import ArithError

def div(numerator, denominator):
    """
    A function to divide a input science image by another image(or flat) or 
    a floating point integer. If the denominator is an AstroData MEF then 
    this function will loop through the SCI, VAR and DQ frames
    to divide each SCI of the numerator by the denominator SCI of 
    the same EXTVER. It will apply a bitwise-or to the DQ frames to 
    preserve their binary formats. 
    
    The VAR frames output will follow:
    
    If denominator is an AstroData instance:
    varOut=sciOut^2 * ( varA/(sciA^2) + varB/(sciB^2) ), 
    where A=numerator and B=denominator frames.
    Else:
    varOut=varA * float^2
            
    If the denominator is a float integer then only the SCI frames of the 
    numerator are each divided by the float.
    
    @param numerator: input image to be divided by the denominator
    @type numerator: a MEF or single extension fits file in the form of an 
                     AstroData instance
    
    @param denominator: denominator to divide the numerator by
    @type denominator:  a MEF of SCI, VAR and DQ frames in the form of an 
                        AstroData instance, a float list, a single float 
                        (list must be in order of the SCI extension EXTVERs) OR 
                        a dictionary of the format 
                        {('SCI',#):##,('SCI',#):##...} where # are the EXTVERs 
                        of the SCI extensions and ## are the corresponding 
                        float values to divide that extension by.
                        
    """
    # Rename inputs to shorter names to save typing
    num = numerator
    den = denominator 
    # Preparing the output astrodata instance
    out = AstroData.prep_output(input_ary=num, clobber=False) 

    # Check to see if the denominator is of type dict, list or float
    if isinstance(den, dict) or isinstance(den, list) or \
    isinstance(den, float):
        """ Creating the dictionary if input is a float or float list 
            Dictionary format will follow:
            {('SCI',#):##,('SCI',#):##...} where # are the EXTVERs 
            of the SCI extensions and ## are the corresponding 
            float values to divide that extension by"""
            
        # Create a dictionary of identical values for each extension if the 
        # input is a single float
        if isinstance(den, float): 
            denDict = {}
            for ext in num['SCI']:
                # Retrieve the EXTVER for this extension
                extver = ext.extver()
                # Add element to the dictionary for this extension
                denDict[('SCI', extver)] = den
                #print repr(denDict)
        # Create a dictionary if the input is a list of floats 
        if isinstance(den, list):    
            denDict = {}
            for ext in num['SCI']:
                extver = ext.extver()
                denDict[('SCI', extver)] = den[extver-1]
                #print repr(denDict)
        # Just rename the variable if denominator is all ready a dictionary
        if isinstance(den, dict):
            denDict = den
        
        # Perform the calculations for when the denominator is a dictionary
        for sci in num['SCI']:
            # Retrieve the extension version for this extension
            extver = sci.extver()
            # Retrieving the float value for this extension from the dictionary
            val = denDict[('SCI', extver)]
            # Start with the out SCI HDU being the current 
            outsci = deepcopy(num[('SCI', extver)]) 
            try:
                # Divide SCI data array by this extensions float value
                outsci.data = np.divide(num[('SCI', extver)].data, val)  
                # Append updated SCI extension to the output
                out.append(outsci)
                # Check there are VAR frames to operate on
                if num.count_exts('VAR') == num.count_exts('SCI'): 
                    # Start with the out VAR HDU being the current 
                    outvar = deepcopy(num[('VAR', extver)])
                    # Multiplying the VAR frames by the float^2
                    outvar.data = np.multiply(num[('VAR', extver)].data, val*val)
                    # Append the updated VAR frame to the output
                    out.append(outvar)
                # Check there are DQ frames to operate on
                if num.count_exts('DQ') == num.count_exts('SCI'):  
                    # Start with the out DQ HDU being the current 
                    outdq = deepcopy(num[('DQ', extver)])
                    # Not changing anything in the DQ frame's data, 
                    # just propagate it to the output
                    out.append(outdq) 
            except:
                raise
            
    # Check to see if the denominator is of type astrodata.AstroData.AstroData
    elif isinstance(den, astrodata.AstroData) or \
                                isinstance(den, astrodata.AstroData.AstroData):
        # Loop through the SCI extensions 
        for sci in num['SCI']:
            # Retrieving the version of this extension
            extver = sci.extver()
            # Start with the out SCI HDU being the current, 
            # we assume there are at least SCI extensions in the input
            outsci = deepcopy(num[('SCI', extver)]) 
        
            try:
                # Making sure arrays are same size/shape
                if num[('SCI', extver)].data.shape == \
                den[('SCI', extver)].data.shape: 
                    # Dividing the numerator SCI frames by those of the 
                    # denominator
                    outsci.data = np.divide(num[('SCI', extver)].data, 
                                          den[('SCI', extver)].data)
                    # Appending the updated SCI frame to the output
                    out.append(outsci)
                    
                    # Check there are an equal numbers of VAR and SCI frames to 
                    # operate on in both the numerator and denominator
                    if num.count_exts('VAR') == den.count_exts('VAR') == \
                    num.count_exts('SCI'): 
                        # Start with the out VAR HDU being the current 
                        outvar = deepcopy(num[('VAR', extver)])
                        
                        # Creating the output VAR frame following 
                        # varOut=sciOut^2 * ( varA/(sciA^2) + varB/(sciB^2) )
                        # using the varianceArrayCalculator() function
                        outvar.data = varutil.varianceArrayCalculator(
                                                      sciExtA=inA['SCI',extver],
                                                      sciExtB=inB['SCI',extver],
                                                      sciOut=outsci,
                                                      varExtA=inA['VAR',extver],
                                                      varExtB=inB['VAR',extver],
                                                      div=True)
                        # Append the updated out VAR frame to the output
                        out.append(outvar)
                        
                    # Check there are an equal number of DQ frames to operate on 
                    if num.count_exts('DQ') == den.count_exts('DQ') == \
                    num.count_exts('SCI'):  
                        # Start with the out DQ HDU being the current 
                        outdq = deepcopy(num[('DQ', extver)])
                                                                  
                        # Perform a bitwise-or 'adding'  on DQ frames 
                        outdq.data = np.bitwise_or(num[('DQ', extver)].data, 
                                                 den[('DQ', extver)].data)
                        # Append the updated out DQ frame to the output
                        out.append(outdq)
                        
                # If arrays are different sizes then raise an exception
                else:
                    raise ArithError('different numbers of SCI, VAR extensions')
            except:
                raise 

    # If the input was not of type astrodata, float, float list or dictionary
    # then raise an exception
    else:
        raise 
    # Return the fully updated output astrodata object      
    return out       
                
def mult(inputA, inputB):
    """
    A function to multiply a input science image by another image(or flat) 
    or a floating point integer. If inputB is an AstroData MEF then this 
    function will loop through the SCI, VAR and DQ frames to multiply each 
    SCI of the inputA by the inputB SCI of the same EXTVER. It will apply a 
    bitwise-or to the DQ frames to preserve their binary formats.
    
    The VAR frames output will follow:
    
    If denominator is an AstroData instance:
    varOut=sciOut^2 * ( varA/(sciA^2) + varB/(sciB^2) ), 
    where A=numerator and B=denominator frames.
    Else:
    varOut=varA * float^2
    
    If inputB is a float integer then only the SCI frames of the inputA 
    are each multiplied by the float.
    
    @param inputA: input image to be multiplied by the inputB
    @type inputA: a MEF or single extension fits file in the form of an 
                  AstroData instance
    
    @param inputB: input to multiply the inputA by
    @type inputB:   a MEF of SCI, VAR and DQ frames in the form of an AstroData 
                    instance, a float list or a single float (list must be 
                    in order of the SCI extension EXTVERs) OR a dictionary 
                    of the format {('SCI',#):##,('SCI',#):##...} 
                    where # are the EXTVERs of the SCI extensions 
                    and ## are the corresponding float values 
                    to multiply that extension by.   
                    
    """
    # Rename inputs to shorter names to save typing
    inA = inputA
    inB = inputB 
    # Preparing the output astrodata instance
    out = AstroData.prep_output(input_ary=inA, clobber=False)

    # Check to see if the denominator is of type dict, list or float
    if isinstance(inB, dict) or isinstance(inB, list) or \
    isinstance(inB, float):
        """ Creating the dictionary if input is a float or float list 
            Dictionary format will follow:
            {('SCI',#):##,('SCI',#):##...} where # are the EXTVERs 
            of the SCI extensions and ## are the corresponding 
            float values to divide that extension by. """
            
        # Create a dictionary of identical values for each extension if the 
        # input is a single float
        if isinstance(inB, float): 
            inBDict = {}
            for ext in inA['SCI']:
                 # Retrieve the EXTVER for this extension
                extver = ext.extver()
                # Add element to the dictionary for this extension
                inBDict[('SCI', extver)] = inB
        # Create a dictionary if the input is a list of floats        
        if isinstance(inB, list):    
            inBDict = {}
            for ext in inA['SCI']:
                extver = ext.extver()
                inBDict[('SCI', extver)] = inB[extver-1]
        # Just rename the variable if denominator is all ready a dictionary
        if isinstance(inB, dict):
            inBDict = inB
        
        # Perform the calculations for when the denominator is a dictionary
        for sci in inA['SCI']:
            # Retrieve the extension version for this extension
            extver = sci.extver()
            # Retrieving the float value for this extension from the dictionary
            val = inBDict[('SCI', extver)]
            # Start with the out SCI HDU being the current 
            outsci = deepcopy(inA[('SCI', extver)]) 
            try:
                # Multiply SCI data array by this extensions float value
                outsci.data=np.multiply(inA[('SCI', extver)].data, val)
                # Append updated SCI extension to the output  
                out.append(outsci)
                # Check there are VAR frames to operate on
                if inA.count_exts('VAR') == inA.count_exts('SCI'): 
                    # Start with the out VAR HDU being the current 
                    outvar = deepcopy(inA[('VAR', extver)])
                    # Multiplying the VAR frames by the float^2
                    outvar.data = np.multiply(inA[('VAR', extver)].data, 
                                              val*val)
                    # Append the updated VAR frame to the output
                    out.append(outvar)
                # Check there are DQ frames to operate on
                if inA.count_exts('DQ') == inA.count_exts('SCI'):   
                    # Start with the out DQ HDU being the current  
                    outdq = deepcopy(inA[('DQ', extver)])
                    # Not changing anything in the DQ frame's data, 
                    # just propagate it to the output
                    out.append(outdq) 
            except:
                raise 
    
    # Check to see if the denominator is of type astrodata.AstroData.AstroData
    elif isinstance(inB, astrodata.AstroData) or \
                                isinstance(inB, astrodata.AstroData.AstroData):
        # Loop through the SCI extensions
        for sci in inA['SCI']:
            # Retrieving the version of this extension
            extver = sci.extver()
            # Start with the out SCI HDU being the current, 
            # we assume there are at least SCI extensions in the input
            outsci = deepcopy(inA[('SCI', extver)]) 
            
            try:
                # Making sure arrays are same size/shape
                if inA[('SCI', extver)].data.shape == \
                inB[('SCI', extver)].data.shape: 
                    #  Multiplying the SCI frames of the inputs
                    outsci.data = np.multiply(inA[('SCI', extver)].data, 
                                            inB[('SCI', extver)].data)
                    # Appending the updated SCI frame to the output
                    out.append(outsci)
                    
                    # Check there are an equal numbers of VAR and SCI frames to 
                    # operate on in both the inputs
                    if inA.count_exts('VAR') == inB.count_exts('VAR') == \
                    inA.count_exts('SCI'): 
                        # Start with the out VAR HDU being the current 
                        outvar = deepcopy(inA[('VAR', extver)])
                        
                        # Creating the output VAR frame following 
                        # varOut=sciOut^2 * ( varA/(sciA^2) + varB/(sciB^2) )
                        # using the varianceArrayCalculator() function
                        outvar.data = varutil.varianceArrayCalculator(
                                                      sciExtA=inA['SCI',extver],
                                                      sciExtB=inB['SCI',extver],
                                                      sciOut=outsci,
                                                      varExtA=inA['VAR',extver],
                                                      varExtB=inB['VAR',extver],
                                                      mult=True)
                        # Append the updated out VAR frame to the output
                        out.append(outvar)
                        
                    # Check there are an equal number of DQ frames to operate on
                    if inA.count_exts('DQ') == inB.count_exts('DQ') == \
                    inA.count_exts('SCI'):   
                        outdq = deepcopy(inA[('DQ', extver)])    
                        # Perform bitwise-or 'adding' DQ frames 
                        outdq.data = np.bitwise_or(inA[('DQ', extver)].data, 
                                                   inB[('DQ', extver)].data)
                        # Append the updated out DQ frame to the output 
                        out.append(outdq)
                # If arrays are different sizes then raise an exception
                else:
                    raise ArithError('different numbers of SCI, VAR extensions')
            except:
                raise 

    # If the input was not of type astrodata, float, float list or dictionary
    # then raise an exception
    else:
        raise    
    # Return the fully updated output astrodata object 
    return out   

def add(inputA, inputB):
    """
    A function to add a input science image to another image or a floating 
    point integer. If inputB is an AstroData MEF then this function will 
    loop through the SCI, VAR and DQ frames to add each SCI of the inputA 
    to the inputB SCI of the same EXTVER. It will apply a bitwise-or to the DQ
    frames to preserve their binary formats. 
    The VAR frames output will follow:
    
    If inputB is an AstroData instance:
    varOut= varA + varB
    Else:
    varOut=varA 
    
    If the inputB is a float integer then only the SCI frames of inputA will 
    each have the float value added, while the VAR and DQ frames of inputA 
    are left alone.
    #$$$$$$$$$$ ARE WE SURE WE DON'T WANT TO OFFER THE ABILITY FOR inputB 
    TO BE A FLOAT LIST OR DICT???????
    
    @param inputA: input image to have inputB added to it
    @type inputA: a MEF or single extension fits file in the form of an 
                  AstroData instance
    
    @param inputB: input to add to the inputA 
    @type inputB: a MEF of SCI, VAR and DQ frames in the form of an AstroData 
                  instance or a float integer 
    #$$$$$ OR A SINGLE EXTENSION FITS FILE TOO???
     
    """
    # Rename inputs to shorter names to save typing
    inA = inputA
    inB = inputB 
    # Preparing the output astrodata instance
    out = AstroData.prep_output(input_ary=inA, clobber=False)
    
    # Check if inputB is of type float, if so, perform the float specific
    # addition calculations     
    if isinstance(inB, float):
        # Loop through the SCI extensions of InputA
        for sci in inA['SCI']:
            # Retrieve the EXTVER for this extension
            extver = sci.extver()
            # Start with the out SCI HDU being the current 
            # we assume there are at least SCI extensions in the input
            outsci = deepcopy(inA[('SCI', extver)]) 
            
            try:
                # Adding the SCI frames by the constant
                outsci.data = np.add(inA[('SCI', extver)].data,inB)
                # Append updated SCI extension to the output 
                out.append(outsci)
                # Appending the inputA VAR and DQ frames un-edited to the output
                # ie no change, just propagate the frames
                
                # Check there are VAR frames to propagate
                if inA.count_exts('VAR') == inA.count_exts('SCI'): 
                    # Start with the out VAR HDU being the current
                    outvar = deepcopy(inA[('VAR', extver)])
                    # Just propagate VAR frames to the output
                    out.append(outvar) 
                # Check there are DQ frames to propagate   
                if inA.count_exts('DQ') == inA.count_exts('SCI'): 
                    # Start with the out DQ HDU being the current 
                    outdq = deepcopy(inA[('DQ', extver)])   
                    # Just propagate DQ frames to the output
                    out.append(outdq) 
            except:
                raise
    # Check to see if the denominator is of type astrodata.AstroData.AstroData
    elif isinstance(inB, astrodata.AstroData) or \
                                isinstance(inB, astrodata.AstroData.AstroData):
        # Loop through the SCI extensions
        for sci in inA['SCI']:
            # Retrieving the version of this extension
            extver = sci.extver()
            # Start with the out SCI HDU being the current, 
            # we assume there are at least SCI extensions in the input
            outsci = deepcopy(inA[('SCI', extver)]) 
            
            try:
                # Making sure arrays are same size/shape
                if inA[('SCI', extver)].data.shape == \
                inB[('SCI', extver)].data.shape: 
                    #  Adding the SCI frames of the inputs
                    outsci.data = np.add(inA[('SCI', extver)].data, 
                                         inB[('SCI', extver)].data)
                    # Appending the updated SCI frame to the output
                    out.append(outsci)
                    
                    # Check there are an equal numbers of VAR and SCI frames to 
                    # operate on in both the inputs
                    if inA.count_exts('VAR') == inB.count_exts('VAR') == \
                    inA.count_exts('SCI'): 
                        # Start with the out VAR HDU being the current 
                        outvar = deepcopy(inA[('VAR', extver)])
                        
                        # Creating the output VAR frame following 
                        # varOut= varA + varB
                        outvar.data = np.add(inA[('VAR', extver)].data, 
                                           inB[('VAR', extver)].data)
                        # Append the updated out VAR frame to the output
                        out.append(outvar)
                        
                    # Check there are an equal number of DQ frames to operate on
                    if inA.count_exts('DQ') == inB.count_exts('DQ') == \
                    inA.count_exts('SCI'):  
                        outdq = deepcopy(inA[('DQ', extver)])   
                        # Performing bitwise-or 'adding' DQ frames 
                        outdq.data = np.bitwise_or(inA[('DQ', extver)].data, 
                                                   inB[('DQ', extver)].data)
                        # Append the updated out DQ frame to the output  
                        out.append(outdq)
                
                # If arrays are different sizes then raise an exception
                else:
                    raise ArithError('different numbers of SCI, VAR extensions')
            except:
                raise 
     
    # If the input was not of type astrodata or float, raise an exception
    else:
        raise             
    # Return the fully updated output astrodata object 
    return out     
        
def sub(inputA, inputB):
    """
    A function to subtract a input science image from another image or a 
    floating point integer. If inputB is an AstroData MEF then this function 
    will loop through the SCI, VAR and DQ frames to subtract each SCI of the 
    inputB from the inputA SCI of the same EXTVER. It will apply a bitwise-or 
    to the DQ frames to preserve their binary formats.
    The VAR frames output will follow:
    
    If inputB is an AstroData instance:
    varOut= varA + varB
    Else:
    varOut=varA 
    
    If the inputB is a float integer then only the SCI frames of inputA will 
    each have the float value subtracted while the VAR and DQ frames of 
    inputA are left alone.
    #$$$$$$$$$$ ARE WE SURE WE DON'T WANT TO OFFER THE ABILITY FOR inputB 
    TO BE A FLOAT LIST OR DICT???????
    
    @param inputA: input image to be subtracted by inputB
    @type inputA: a MEF or single extension fits file in the form of an 
                  AstroData instance
    
    @param inputB: inputB to subtracted from inputA 
    @type inputB: a MEF of SCI, VAR and DQ frames in the form of an AstroData 
                  instance or a float int 
    #$$$$$ OR A SINGLE EXTENSION FITS FILE TOO???
    
    """
    # Rename inputs to shorter names to save typing
    inA = inputA
    inB = inputB 
    # Preparing the output astrodata instance
    out=AstroData.prep_output(input_ary = inA, clobber = False)
    
    # Check if inputB is of type float, if so, perform the float specific
    # addition calculations
    if isinstance(inB, float):
        # Loop through the SCI extensions of InputA
        for sci in inA['SCI']:
            # Retrieve the EXTVER for this extension
            extver = sci.extver()
            # Start with the out SCI HDU being the current 
            # we assume there are at least SCI extensions in the input
            outsci = deepcopy(inA[('SCI', extver)]) 
            
            try:
                # Subtracting the SCI frames by the constant
                outsci.data = np.subtract(inA[('SCI', extver)].data, inB)
                # Append updated SCI extension to the output 
                out.append(outsci)
                
                # Appending the inputA VAR and DQ frames un-edited to the output
                # ie no change, just propagate the frames
                
                # Check there are VAR frames to propagate
                if inA.count_exts('VAR') == inA.count_exts('SCI'): 
                    # Start with the out VAR HDU being the current
                    outvar = deepcopy(inA[('VAR', extver)])
                    # Just propagate VAR frames to the output
                    out.append(outvar) 
                    # ie there are DQ frames to operate on 
                if inA.count_exts('DQ') == inA.count_exts('SCI'): 
                    # Start with the out DQ HDU being the current 
                    outdq = deepcopy(inA[('DQ', extver)]) 
                    # Just propagate DQ frames to the output  
                    out.append(outdq) 
            except:
                raise
            
    # Check to see if the denominator is of type astrodata.AstroData.AstroData
    elif isinstance(inB, astrodata.AstroData) or \
                                isinstance(inB, astrodata.AstroData.AstroData):
        # Loop through the SCI extensions
        for sci in inA['SCI']:
            # Retrieving the version of this extension
            extver = sci.extver()  
            # Start with the out SCI HDU being the current,
            # we assume there are at least SCI extensions in the input    
            outsci = deepcopy(inA[('SCI', extver)])    
               
            try:
                # Making sure arrays are same size/shape
                if inA[('SCI', extver)].data.shape == \
                inB[('SCI', extver)].data.shape: 
                    #  Subtracting the SCI frames
                    outsci.data = np.subtract(inA[('SCI', extver)].data, 
                                              inB[('SCI', extver)].data)
                    out.append(outsci)
                    
                    # Check there are an equal numbers of VAR frames to 
                    # operate on
                    if inA.count_exts('VAR') == inB.count_exts('VAR') == \
                    inA.count_exts('SCI'): 
                        # Start with the out VAR HDU being the current 
                        outvar = deepcopy(inA[('VAR', extver)])
                        # Creating the output VAR frame following
                        # varOut= varA + varB
                        outvar.data = np.add(inA[('VAR', extver)].data, 
                                           inB[('VAR', extver)].data)
                        # Append the updated out VAR frame to the output
                        out.append(outvar)
                    # Check there are an equal number of DQ frames to operate on
                    if inA.count_exts('DQ') == inB.count_exts('DQ') == \
                    inA.count_exts('SCI'):  
                        # Start with the out DQ HDU being the current
                        outdq = deepcopy(inA[('DQ', extver)])       
                        # Performing bitwise-or 'adding' DQ frames 
                        outdq.data = np.bitwise_or(inA[('DQ', extver)].data, 
                                                 inB[('DQ', extver)].data)
                        # Append the updated out DQ frame to the output 
                        out.append(outdq)
                
                # If arrays are different sizes then raise an exception
                else:
                    raise ArithError('different numbers of SCI, VAR extensions')
            except:
                raise 
     
    # If the input was not of type astrodata or float, raise an exception
    else:
        raise            
    # Return the fully updated output astrodata object 
    return out 

