################################################################################

#Tools for retrieving results from CFD-Post

#Stadia42, Bradford Lynch, 2014, Chicago, IL

################################################################################
import subprocess

def runSessionOnResultsFile(sessionFileName, resultsFileName):
    '''
    Calls CFX post processor on resultsFileName using the session file given by
    sessionFileName
    '''
    subprocess.call(['cfx5post', '-batch', sessionFileName, resultsFileName], shell=True)

    return

################################################################################

#Objects for creating CFD-Post session files

################################################################################

class SessionFile(object):
    def __init__(self, sections=[]):
        self.sections = sections
        
    def addSection(self, section):
        self.sections.append(section)
        
    def getDefinition(self):
        sessionDef = [ 'COMMAND FILE:',
        '  CFX Post Version = 15.0',
        'END']
        
        for section in self.sections:
            sessionDef.extend(section.getDefinition())
            
        return sessionDef
        
    def writeSessionFile(self, sessionFileName):
        newFile = open(sessionFileName, 'wb')
        
        sessionFileText = self.getDefinition()
        
        for line in sessionFileText:
            newFile.write(line + '\n')
            
        newFile.close()
        
        
class Chart(object):
    def __init__(self, name, xVariable='X', yVariable='Pressure'):
        self.name = name
        self.xVar = xVariable
        self.yVar = yVariable
        self.series = []
        self.numOfSeries = 0
        
    def addSeries(self, seriesName, location):
        self.numOfSeries += 1
        seriesNum = self.numOfSeries
        self.series.append(Series(location, seriesName, seriesNum, self.xVar, self.yVar))
        
    def getDefinition(self):
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
        '  Default X Variable Boundary Values = Hybrid',
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
            chartDef.extend(serie.getDefinition())
        
        chartEnd = [ '  OBJECT REPORT OPTIONS:',
        '    Report Caption =',
        '  END',
        'END']

        chartDef.extend(chartEnd)

        return chartDef
        
class Series(object):
    def __init__(self, location, seriesName, seriesNumber, xVariable, yVariable):
        self.loc = location
        self.name = seriesName
        self.num = seriesNumber
        self.xVar = xVariable
        self.yVar = yVariable
        
    def getDefinition(self):
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
    def __init__(self, name, point1, point2):
        self.name = name
        self.p1 = point1
        self.p2 = point2
        
    def getDefinition(self):
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
        
class Export(object):
    def __init__(self, chartObj, exportLocation, overwrite='On'):
        self.chart = chartObj
        self.loc = exportLocation
        self.overwrite = overwrite
        
    def getDefinition(self):
        exportDef = [ 'EXPORT:',
        '  Export File = ' + self.loc,
        '  Export Chart Name = ' + self.chart.name,
        '  Overwrite = ' + self.overwrite,
        'END',
        '>export chart',]
        
        return exportDef
