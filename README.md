cfd_tools
=========

Tools for running computational fluid dynamics analysis and post-processing results

Notes regarding the use of 'automated_ansys_post_processing.py'
===============================================================
Class 'CaseSweep' is used to define a sweep of cases or design points in Ansys Workbench. Included is a class 'FlapperDesignSweep' derived from 'CaseSweep' which has a customized method for writing out the session file used to post-process the CFD results. This method is specially aimed at analysing a "FlapperValve". The session file written out will create and save pressure and velocity contour plots, create several line probes through the valve flow area, and export the pressure along these lines. This method can be readily adapted for processing of other cases but note that there are three keys hard coded into the method:

'P16 - UseRe'
This key is used in the CFD analysis to determine what the inlet pressure is. If is set to '0' then the inlet pressure is simply set by 'P17 - Pinlet', if it is set to '1' then the parameter 'P12 - Re' (The desired Reynolds number of the flow through the valve), the valve geometry, and fluid properties are used to calculate an inlet pressure that gives the desired Reynolds number.

'P17 - Pinlet'
This key is used to set the maximum of the range in the pressure contour plots when 'P16 - UseRe' is equal to 0.  Otherwise, it is unused.

'P15 - lift'
This key is used to set the Y location of the line probes through the valve flow area. The variable 'numLines' determines the number of lines to be drawn through the flow area. The lines are evenly spaced based on the lift 'P15 - lift' and the number of lines 'numLines'.