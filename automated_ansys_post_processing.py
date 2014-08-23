################################################################################

#Tools for retrieving results from CFD-Post

#Stadia42, Bradford Lynch, 2014, Chicago, IL

################################################################################
import subprocess, csv, os

################################################################################

#General helper functions

################################################################################

def runSessionOnResultsFile(sessionFileName, resultsFileName):
    '''
    Calls CFX post processor on resultsFileName using the session file given by
    sessionFileName
    '''
    subprocess.call(['cfx5post', '-batch', sessionFileName, resultsFileName], shell=True)

    return
    
################################################################################

#Objects for defining cases of CFD runs

################################################################################

class CaseSweep(object):
    '''
    Object defining a sweep of different CFD cases. The sweepDefinitionFile must
    be a CSV file with a table of the cases that were run; this can be copied 
    directly from Ansys Workbench
    '''
    def __init__(self, sweepDefinitionFile, rootDirectory, modelName):
        self.sweepFile = sweepDefinitionFile
        self.rootDir = rootDirectory
        self.modelName = modelName
        self.sweepHeaders = {}
        self.sweepDict = {}
        self.sweepCaseResults = {}

        #Read sweep definition file
        self.readSweepDefFile()
        
    def readSweepDefFile(self):
        '''
        Reads the sweep definition file into two dictionaries. The first uses
        the column index of the CSV file as a key to the column name. The 
        second uses the column name as a key to the list of values in the column
        
        sweepHeaders contains the Column Index -> Column Name
        sweepDict contains the Column Name -> List of Values
        '''
        i = 0
        with open(self.sweepFile, 'rb') as csvFile:
            sweepData = csv.reader(csvFile, delimiter=',')
            
            for row in sweepData:
                if i == 0:
                    #This is the header row. Use values for keys in sweepDict
                    col = 0
                    for cell in row:
                        self.sweepHeaders[col] = cell
                        self.sweepDict[cell] = []
                        col += 1

                elif i == 1:
                    #This is the units row. Do nothing for now
                    pass
                else:
                    col = 0
                    for cell in row:
                        try:
                            #Try to convert the cell value to a float
                            cell = float(cell)
                        except ValueError:
                            #Leave the value alone if it is not a float
                            pass
                        
                        self.sweepDict[self.sweepHeaders[col]].append(cell)

                        col += 1
                        
                i += 1
                
    def writeSessionFile(self, sessionFileName, designPointIndex):
        '''
        Method to write out a CFD-Post session file. In the base class this is
        not implemented because it is highly dependent on the CFD cases that
        were run.
        '''
        
        raise NotImplementedError
        
    def processResults(self, designPointColumnName):
        '''
        Steps through list of cases and runs the session file on the case results
        '''
        #Step through design points
        for dpIndex in range(len(self.sweepDict[designPointColumnName])):
            designPoint = self.sweepDict[designPointColumnName][dpIndex]
            #Determine the working directory
            if designPoint == 'Current':
                designPoint = 'dp0'
                dpDir = self.rootDir + '\\' + self.modelName + '_files'
                
            else:
                designPoint = designPoint.replace(' ', '').lower()
                dpDir = self.rootDir + '\\' + self.modelName + '_' + designPoint + '_files'
                
            #Change to the design point directory, then to the results directory
            os.chdir(dpDir)
            os.chdir(designPoint + '\\CFX-1\\CFX')
            
            #Determine the latest results file
            files = os.listdir('.')
            files.reverse()  #Reversing the order because the files are listed lowest number to highest number and we want the highest number
            for fileName in files:
                if fileName.split('.')[-1] == 'res':
                    resultsFile = fileName
                    
                    #Exit loop after finding the latest file
                    break
                    
            #Write a session file
            sessionFileName = 'Post' + str(designPoint) + '.cse'
            self.writeSessionFile(sessionFileName, dpIndex)
            
            #Call CFD-Post on the results file
            print 'Processing Design Point ' + str(dpIndex)
            runSessionOnResultsFile(sessionFileName, resultsFile)
            
            #Return to the root directory
            os.chdir(self.rootDir)
            
            #Read results file
            
    def readResultFiles(self, designPointColumnName):
        '''
        Reads CSV result files into CaseResult objects
        '''
        #Sweep design points
        for dpIndex in range(len(self.sweepDict[designPointColumnName])):
            #Set the filename for the current design point
            dpFileName = 'results_from_dp' + str(dpIndex) + '.csv'
            
            #Get the case setup for the design point
            caseSetup = {}
            for key in self.sweepDict.keys():
                caseSetup[key] = self.sweepDict[key][dpIndex]
                
            self.sweepCaseResults[dpIndex] = CaseResult(caseSetup, dpFileName)
            
    def plotCaseResults(self, designPoint, dataset):
        raise NotImplementedError
            
        
class FlapperDesignSweep(CaseSweep):
    '''
    This class is derived from CaseSweep and has a custom method
    writeSessionFile that writes out a session file to collect results
    that are specific to the analysis of a flapper valve.
    
    The method is specialized further by relying on the parameter 'P16 - UseRe'
    that tells Ansys to run a constant pressure drop (If UseRe = 0) or to run
    a case with a specific Reynolds number (If UseRe = 1).  When saving results,
    we want the range to be fixed for the constant pressure drop cases but scaled
    for the constant Re cases.
    '''
    def writeSessionFile(self, sessionFileName, dpIndex):
        #Set the directory to save the results
        resultsDir = self.rootDir + '\\sweepResults'
        
        #Create a new session file object
        session = SessionFile([])
        
        #Hide model wireframe
        session.addSection(VisibilityAction('/WIREFRAME:Wireframe', '/VIEW:View 1', 'hide'))
        
        #Orient view
        #NOTE: This is highly dependent on your model. It is best to create this
        #by recording a session in CFD-Post where you orient the model accordingly
        session.addSection(View('View 1', [-2.69195e-006, 0.000327419, 0.00225109], 555.248, [-3.16153e-005, -0.000739617], [0, 0.707107, 0, 0.707107]))
        
        #Set the location and filename of the pressure contour
        locToSaveContour = resultsDir + '\\pressure_contour_dp'+ str(dpIndex) + '.png'
        
        #Determine which scale to use for the contour
        if self.sweepDict['P16 - UseRe'][dpIndex] == 0:  #The key for the flag for constant pressure or Re is hard coded!
            contourRange = (0, self.sweepDict['P17 - Pinlet'][dpIndex])  #The key for the flag for the inlet pressure is hard coded!
        else:
            contourRange = 'Local'
        
        #Add the pressure contour
        session.addContour('Pressure Contour', 'symmetry', 'Pressure', locToSaveContour, contourRange=contourRange)
        
        #Add a velocity contour
        locToSaveContour = resultsDir + '\\velocity_contour_dp'+ str(dpIndex) + '.png'
        session.addContour('Velocity Contour', 'symmetry', 'Velocity', locToSaveContour)
        
        #Get the lift value for this case
        #NOTE that the key for the lift has been hard coded
        lift = self.sweepDict['P15 - lift'][dpIndex]
        
        #Create line objects to probe mesh quantities from
        lines = []
        numLines = 5
        dLift = lift/float(numLines)
        
        for i in range(numLines):
            name = 'layer' + str(i)
            yPos = lift - dLift/2. - i*dLift
            p1 = [0, yPos, 0]
            p2 = [1, yPos, 0]
            line = Line(name, p1, p2)
            
            lines.append(line)
            
        #Create a chart object to plot the data
        probedData = Chart('Chart' + str(dpIndex), 'X', 'Pressure')
        
        #Add series for lines
        for line in lines:
            probedData.addSeries(line.name, line)
            
        #Create an export object
        export = Export(probedData, resultsDir + '\\results_from_dp' + str(dpIndex) + '.csv')
            
        #Create the session object
        session.addSection(lines)
        session.addSection(probedData)
        session.addSection(export)
        
        #Write the session file
        session.writeSessionFile(sessionFileName)
        
################################################################################

#Objects for viewing and processing case results

################################################################################

class CaseResult(object):
    '''
    Object with special methods for collecting and viewing results along a line
    exported from Ansys CFD-Post
    '''
    def __init__(self, caseSetup, caseResultsFile):
        self.caseSetup = caseSetup
        self.results = {}
        
        self.readCaseResults(caseResultsFile)
        
    def readCaseResults(self, caseResultsFile):
        caseResults = []
        
        with open(caseResultsFile, 'rb') as caseResultsCSV:
            caseResultsReader = csv.reader(caseResultsCSV, delimiter=',')
            for row in caseResultsReader:
                caseResults.append(row)    
        
        i = 0
        
        while i < len(caseResults):
            if caseResults[i] == []:
                i += 1
                
            elif caseResults[i] == ['[Name]']:
                datasetName = caseResults[i+1][0]
                i += 2

            elif caseResults[i] == ['[Data]']:
                xHeaders = caseResults[i+1][0].split()
                yHeaders = caseResults[i+1][1].split()
                
                self.results[datasetName] = Dataset(datasetName, xHeaders[0], xHeaders[2], yHeaders[0], yHeaders[2])
                i += 2
                
            else:
                try:
                    x = float(caseResults[i][0])
                    y = float(caseResults[i][1])
                    self.results[datasetName].addDataPoint(x, y)
                    i += 1
                except ValueError:
                    i += 1
                     
        
class Dataset(object):
    '''
    Defines a dataset object with X and Y labels and data
    '''
    def __init__(self, name, xLabel, xUnit, yLabel, yUnit):
        self.name = name
        self.xLabel = xLabel
        self.xUnit = xUnit
        self.x = []
        self.yLabel = yLabel
        self.yUnit = yUnit
        self.y = []
        
    def addDataPoint(self, x, y):
        '''
        Adds the data point (x, y) to the end of the dataset
        '''
        self.x.append(x)
        self.y.append(y)
        

################################################################################

#Objects for creating Ansys CFD-Post session files

################################################################################

class SessionFile(object):
    '''
    Object defining an Ansys CFD-Post session file.  Each section of the session
    file is defined by its respective object and should be added to the list of
    sections "self.sections".  Be default, this is initialized to None
    '''
    def __init__(self, sections=[]):
        self.sections = sections
        
    def addSection(self, section):
        '''
        Adds a section or a list of sections to the session file
        '''
        if type(section) != list:
            self.sections.append(section)
        else:
            self.sections.extend(section)
        
    def getDefinition(self):
        '''
        Returns the defined session file as a list of lines (Without EOL markers)
        '''
        sessionDef = [ 'COMMAND FILE:',
        '  CFX Post Version = 15.0',
        'END']
        
        for section in self.sections:
            sessionDef.extend([' '])
            sessionDef.extend(section.getDefinition())
            
        return sessionDef
        
    def writeSessionFile(self, sessionFileName):
        '''
        Writes the defined session file to the current working directory.  This
        session file is ready to be used with CFD-Post 'as is'
        '''
        newFile = open(sessionFileName, 'wb')
        
        sessionFileText = self.getDefinition()
        
        for line in sessionFileText:
            newFile.write(line + '\n')
            
        newFile.close()
        
    def addContour(self, name, location, variable, fileName, contourRange='Local', size=(1280, 1024)):
        '''
        Adds a contour of 'variable' on 'location' and saves it to disk at
        'fileName'. Setting fileName = False will prevent saving of the contour
        '''
        #Create a contour of the variable
        self.addSection(Contour(name, variable, location, contourRange))
        
        #Turn on the pressure contour, save a copy of it, then hide it
        self.addSection(VisibilityAction('/CONTOUR:' + name, '/VIEW:View 1', 'show'))
        self.addSection(Hardcopy(fileName, size))
        self.addSection(VisibilityAction('/CONTOUR:' + name, '/VIEW:View 1', 'hide'))
        
class SessionSectionFromFile(object):
    '''
    Defines a section of a session file (Or an entire session file) by reading
    it in from a file.
    
    File 'sectionFile' bust be present in the working directory when the object
    is created.  After that, the object is portable and doesn't require the file.
    '''
    def __init__(self, sectionFile):
        self.sectionFile = sectionFile
        self.readSectionFile()
        
    def readSectionFile(self):
        with open(self.sectionFile, 'rb') as sectionTextFile:
            self.sectionFileData = sectionTextFile.read().splitlines()
            
    def getDefinition(self):
        return self.sectionFileData
        
class Chart(object):
    '''
    Defines a chart named 'name' in the session file.  The default x-axis and 
    y-axis variables must be defined.
    '''
    def __init__(self, name, xVariable='X', yVariable='Pressure'):
        self.name = name
        self.xVar = xVariable
        self.yVar = yVariable
        self.series = []
        self.numOfSeries = 0
        
    def addSeries(self, seriesName, location):
        '''
        Adds a series to the chart. The 'location' should be a line object.
        '''
        self.numOfSeries += 1
        seriesNum = self.numOfSeries
        self.series.append(Series(location, seriesName, seriesNum, self.xVar, self.yVar))
        
    def getDefinition(self):
        '''
        Returns the defined chart as a list of lines (Without EOL markers)
        '''
        chartLinesOrder = ''
        
        for n in range(self.numOfSeries):
            chartLinesOrder += 'Series ' + str(n + 1) + ',Chart Line ' + str(n + 1)
            
            if n + 1 < self.numOfSeries:
                chartLinesOrder += ','
            
        
        chartDef = [ 'CHART:' + self.name,
        '  Chart Axes Font = Tahoma, 10, False, False, False, False',
        '  Chart Axes Titles Font = Tahoma, 10, True, False, False, False',
        '  Chart Grid Line Width = 1',
        '  Chart Horizontal Grid = On',
        '  Chart Legend = On',
        '  Chart Legend Font = Tahoma, 8, False, False, False, False',
        '  Chart Legend Inside = Outside Chart',
        '  Chart Legend Justification = Center',
        '  Chart Legend Position = Bottom',
        '  Chart Legend Width Height = 0.2 , 0.4',
        '  Chart Legend X Justification = Right',
        '  Chart Legend XY Position = 0.73 , 0.275',
        '  Chart Legend Y Justification = Center',
        '  Chart Line Width = 2',
        '  Chart Lines Order = ' + chartLinesOrder,
        '  Chart Minor Grid = Off',
        '  Chart Minor Grid Line Width = 1',
        '  Chart Symbol Size = 4',
        '  Chart Title = ' + self.name,
        '  Chart Title Font = Tahoma, 12, True, False, False, False',
        '  Chart Title Visibility = On',
        '  Chart Type = XY',
        '  Chart Vertical Grid = On',
        '  Chart X Axis Automatic Number Formatting = On',
        '  Chart X Axis Label = X Axis <units>',
        '  Chart X Axis Number Format = %10.3e',
        '  Chart Y Axis Automatic Number Formatting = On',
        '  Chart Y Axis Label = Y Axis <units>',
        '  Chart Y Axis Number Format = %10.3e',
        '  Default Chart X Variable = ' + self.xVar,
        '  Default Chart Y Variable = ' + self.yVar,
        '  Default Histogram Y Axis Weighting = None',
        '  Default Time Chart Variable = ' + self.yVar,
        '  Default Time Chart X Expression = Time',
        '  Default Time Variable Absolute Value = Off',
        '  Default Time Variable Boundary Values = Conservative',
        '  Default X Variable Absolute Value = Off',
        '  Default X Variable Boundary Values = Conservative',
        '  Default Y Variable Absolute Value = Off',
        '  Default Y Variable Boundary Values = Conservative',
        '  FFT Full Input Range = On',
        '  FFT Max = 0.0',
        '  FFT Min = 0.0',
        '  FFT Subtract Mean = Off',
        '  FFT Window Type = Hanning',
        '  FFT X Function = Frequency',
        '  FFT Y Function = Power Spectral Density',
        '  Histogram Automatic Divisions = Automatic',
        '  Histogram Divisions = -1.0,1.0',
        '  Histogram Divisions Count = 10',
        '  Histogram Y Axis Value = Count',
        '  Is FFT Chart = Off',
        '  Max X = 1.0',
        '  Max Y = 1.0',
        '  Min X = -1.0',
        '  Min Y = -1.0',
        '  Time Chart Keep Single Case = Off',
        '  Use Data For X Axis Labels = On',
        '  Use Data For Y Axis Labels = On',
        '  X Axis Automatic Range = On',
        '  X Axis Inverted = Off',
        '  X Axis Logarithmic Scaling = Off',
        '  Y Axis Automatic Range = On',
        '  Y Axis Inverted = Off',
        '  Y Axis Logarithmic Scaling = Off']
        
        for serie in self.series:
            chartDef.extend([' '])
            chartDef.extend(serie.getDefinition())
        
        chartEnd = [' ',
        '  OBJECT REPORT OPTIONS:',
        '    Report Caption =',
        '  END',
        'END']

        chartDef.extend(chartEnd)

        return chartDef
        
class Series(object):
    '''
    Defines a series object of name 'seriesName' and number 'seriesNumber'. The
    location must be a line object. The xVariable and yVariable should be strings
    corresponding to quantities in the CFD model.
    '''
    def __init__(self, location, seriesName, seriesNumber, xVariable, yVariable):
        self.loc = location
        self.name = seriesName
        self.num = seriesNumber
        self.xVar = xVariable
        self.yVar = yVariable
        
    def getDefinition(self):
        '''
        Returns the series object definition as a list of lines (Without EOL markers)
        '''
        seriesDef = ['  CHART SERIES:Series ' + str(self.num),
        '    Chart Line Custom Data Selection = Off',
        '    Chart Line Filename =',
        '    Chart Series Type = Regular',
        '    Chart X Variable = ' + self.xVar,
        '    Chart Y Variable = ' + self.yVar,
        '    Histogram Y Axis Weighting = None',
        '    Location = /LINE:' + self.loc.name,
        '    Series Name = ' + self.name,
        '    Time Chart Expression = Time',
        '    Time Chart Type = Point',
        '    Time Chart Variable = ' + self.yVar,
        '    Time Chart X Expression = Time',
        '    Time Variable Absolute Value = Off',
        '    Time Variable Boundary Values = Conservative',
        '    X Variable Absolute Value = Off',
        '    X Variable Boundary Values = Conservative',
        '    Y Variable Absolute Value = Off',
        '    Y Variable Boundary Values = Conservative',
        '    CHART LINE:Chart Line ' + str(self.num),
        '      Auto Chart Line Colour = On',
        '      Chart Line Colour = 1.0, 0.0, 0.0',
        '      Chart Line Style = Automatic',
        '      Chart Line Visibility = On',
        '      Chart Symbol Colour = 0.0, 1.0, 0.0',
        '      Chart Symbol Style = None',
        '      Fill Area = On',
        '      Fill Area Options = Automatic',
        '      Is Valid = True',
        '      Line Name = ' + self.loc.name,
        '      Use Automatic Line Naming = On',
        '    END',
        '  END']
        
        return seriesDef
        
class Line(object):
    '''
    Defines a line object with name 'name'.  'point1' and 'point2' must be one
    dimensional arrays of length 3 defining the location of each point in R3.
    The line is defined as passing through the two points specified.
    '''
    def __init__(self, name, point1, point2):
        self.name = name
        self.p1 = point1
        self.p2 = point2
        
    def getDefinition(self):
        '''
        Returns the line object definition as a list of lines (Without EOL markers)
        '''
        p1String = str(self.p1[0]) + ' [m], ' + str(self.p1[1]) + ' [m], ' + str(self.p1[2]) + ' [m]'
        p2String = str(self.p2[0]) + ' [m], ' + str(self.p2[1]) + ' [m], ' + str(self.p2[2]) + ' [m]'
        lineDef = ['LINE:' + self.name,
        '  Apply Instancing Transform = On',
        '  Colour = 1, 1, 0',
        '  Colour Map = Default Colour Map',
        '  Colour Mode = Constant',
        '  Colour Scale = Linear',
        '  Colour Variable = Pressure',
        '  Colour Variable Boundary Values = Hybrid',
        '  Domain List = /DOMAIN GROUP:All Domains',
        '  Instancing Transform = /DEFAULT INSTANCE TRANSFORM:Default Transform',
        '  Line Samples = 10',
        '  Line Type = Cut',
        '  Line Width = 2',
        '  Max = 0.0 [Pa]',
        '  Min = 0.0 [Pa]',
        '  Option = Two Points',
        '  Point 1 = ' + p1String,
        '  Point 2 = ' + p2String,
        '  Range = Global',
        '  OBJECT VIEW TRANSFORM:',
        '    Apply Reflection = Off',
        '    Apply Rotation = Off',
        '    Apply Scale = Off',
        '    Apply Translation = Off',
        '    Principal Axis = Z',
        '    Reflection Plane Option = XY Plane',
        '    Rotation Angle = 0.0 [degree]',
        '    Rotation Axis From = 0 [m], 0 [m], 0 [m]',
        '    Rotation Axis To = 0 [m], 0 [m], 0 [m]',
        '    Rotation Axis Type = Principal Axis',
        '    Scale Vector = 1 , 1 , 1',
        '    Translation Vector = 0 [m], 0 [m], 0 [m]',
        '    X = 0.0 [m]',
        '    Y = 0.0 [m]',
        '    Z = 0.0 [m]',
        '  END',
        'END']

        return lineDef
        
class Contour(object):
    '''
    Defines a contour object with name 'name', shaded based on 'variable' and
    on 'location'. By default the contour range is set by the local minimum and
    maximum values. A user specified range can be set by providing a tuple of
    (rangeMin, rangeMax) for 'contourRange'
    
    NOTE: Only the variable types 'Pressure' and 'Velocity' are supported with
    user-defined ranges
    '''
    def __init__(self, name, variable, location, contourRange='Local'):
        self.name = name
        self.var = variable
        self.location = location
        self.range = contourRange
        
    def getDefinition(self):
        '''
        Returns the contour object definition as a list of lines (Without EOL markers)
        '''
        if self.range == 'Local':
            contourRangeStr = 'Local'
            rangeMin = 0.0
            rangeMax = 0.0
        elif type(self.range) == tuple and len(self.range) == 2:
            contourRangeStr = 'User Specified'
            rangeMin, rangeMax = self.range
        else:
            raise ValueError('Variable contourRange must be "Local" or a tuple of the range min and max')
            
        if self.var == 'Pressure':
            units = '[Pa]'
        elif self.var == 'Velocity':
            units = '[m s^-1]'
        elif self.range != 'Local':
            raise ValueError('Only the variables "Pressure" and "Velocity" are supported for user-defined ranges')
        else:
            units = '[m s^-1]'
            
        contourDef = ['CONTOUR:' + self.name,
        '  Apply Instancing Transform = On',
        '  Clip Contour = Off',
        '  Colour Map = Default Colour Map',
        '  Colour Scale = Linear',
        '  Colour Variable = ' + self.var,
        '  Colour Variable Boundary Values = Hybrid',
        '  Constant Contour Colour = Off',
        '  Contour Range = ' + contourRangeStr,
        '  Culling Mode = No Culling',
        '  Domain List = /DOMAIN GROUP:All Domains',
        '  Draw Contours = On',
        '  Font = Sans Serif',
        '  Fringe Fill = On',
        '  Instancing Transform = /DEFAULT INSTANCE TRANSFORM:Default Transform',
        '  Lighting = On',
        '  Line Colour = 0, 0, 0',
        '  Line Colour Mode = Default',
        '  Line Width = 1',
        '  Location List = ' + self.location,
        '  Max = ' + str(rangeMax) + ' ' + units,
        '  Min = ' + str(rangeMin) + ' ' + units,
        '  Number of Contours = 11',
        '  Show Numbers = Off',
        '  Specular Lighting = On',
        '  Surface Drawing = Smooth Shading',
        '  Text Colour = 0, 0, 0',
        '  Text Colour Mode = Default',
        '  Text Height = 0.024',
        '  Transparency = 0.0',
        '  Value List = 0 [m s^-1],1 [m s^-1]',
        '  OBJECT VIEW TRANSFORM:',
        '    Apply Reflection = Off',
        '    Apply Rotation = Off',
        '    Apply Scale = Off',
        '    Apply Translation = Off',
        '    Principal Axis = Z',
        '    Reflection Plane Option = XY Plane',
        '    Rotation Angle = 0.0 [degree]',
        '    Rotation Axis From = 0 [m], 0 [m], 0 [m]',
        '    Rotation Axis To = 0 [m], 0 [m], 0 [m]',
        '    Rotation Axis Type = Principal Axis',
        '    Scale Vector = 1 , 1 , 1',
        '    Translation Vector = 0 [m], 0 [m], 0 [m]',
        '    X = 0.0 [m]',
        '    Y = 0.0 [m]',
        '    Z = 0.0 [m]',
        '  END',
        'END']
        
        return  contourDef
        
class Export(object):
    '''
    Defines an export object for the chart 'chartObj'. The exported data will be
    saved to the location given by 'exportLocation'.
    '''
    def __init__(self, chartObj, exportLocation, overwrite='On'):
        self.chart = chartObj
        self.loc = exportLocation
        self.overwrite = overwrite
        
    def getDefinition(self):
        '''
        Returns the export definition as a list of lines (Without EOL markers)
        '''
        exportDef = [ 'EXPORT:',
        '  Export File = ' + self.loc,
        '  Export Chart Name = ' + self.chart.name,
        '  Overwrite = ' + self.overwrite,
        'END',
        '>export chart',]
        
        return exportDef
        
class Hardcopy(object):
    '''
    Defines a hardcopy object which is responsible for saving the viewport to an
    image file such as a png
    
    fileName must be the path to save the file, such as 'C:/Users/foo/Pressure.png'
    imageSize must be a tuple of list of the image width, height
    '''
    def __init__(self, fileName, imageSize):
        self.fileName = fileName
        self.imageSize = imageSize
        
    def getDefinition(self):
        hardcopyDef = [ 'HARDCOPY:',
        '  Antialiasing = On',
        '  Hardcopy Filename = ' + self.fileName,
        '  Hardcopy Format = png',
        '  Hardcopy Tolerance = 0.0001',
        '  Image Height = ' + str(self.imageSize[1]),
        '  Image Scale = 100',
        '  Image Width = ' + str(self.imageSize[0]),
        '  JPEG Image Quality = 100',
        '  Screen Capture = Off',
        '  Use Screen Size = Off',
        '  White Background = On',
        'END',
        '>print']
        
        return hardcopyDef

class View(object):
    def __init__(self, name, pivotPoint, scale, pan, rotation):
        self.name = name
        self.pivot = pivotPoint
        self.scale = scale
        self.pan = pan
        self.rot = rotation
        
    def getDefinition(self):
        viewDef = [ 'VIEW:' + self.name,
        '  Camera Mode = User Specified',
        '  CAMERA:',
        '    Option = Pivot Point and Quaternion',
        '    Pivot Point = ' + str(self.pivot)[1:-1],  #Is a list, so we need to slice of the brackets
        '    Scale = ' + str(self.scale),
        '    Pan = ' + str(self.pan)[1:-1],  #Is a list, so we need to slice of the brackets
        '    Rotation Quaternion = ' + str(self.rot)[1:-1],  #Is a list, so we need to slice of the brackets
        '  END',
        '  ',
        'END']
        
        return viewDef

class VisibilityAction(object):
    '''
    Defines a visibility action for the CFD-Post viewport. 'graphicsObject' must
    be an object defined in CFD-Post such as '/CONTOUR:Pressure Contour' and 
    'view' must be a view or figure such as '/VIEW:View 1'. 'viewStatus' must
    be set to 'show' or 'hide'
    '''
    def __init__(self, graphicsObject, view, viewStatus):
        self.gfxObj = graphicsObject
        self.view = view
        self.viewStatus = viewStatus
        
    def getDefinition(self):
        '''
        Returns the view definition as a list of lines (Without EOL markers)
        '''
        viewDef = ['# Sending visibility action from ViewUtilities',
        '>' + self.viewStatus + ' ' + self.gfxObj + ', view=' + self.view]
        
        return viewDef
