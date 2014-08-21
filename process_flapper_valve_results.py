################################################################################

#Script to process CFD on flapper valve designs

#Stadia42, Bradford Lynch, 2014, Chicago, IL

################################################################################
import automated_ansys_post_processing as ansysPP

class FlapperDesignSweep(ansysPP.CaseSweep):
    def writeSessionFile(self, sessionFileName, dpIndex):
        #Get the lift value for this case
        #NOTE that the key for the lift has been hard coded
        lift = self.sweepDict['P15 - lift'][dpIndex]
        
        #Create line objects to probe mesh quantities from
        lines = []
        numLines = 5
        
        for i in range(numLines):
            name = 'layer' + str(i)
            yPos = lift * (1 - float(i)/(float(numLines) + 1))
            p1 = [0, yPos, 0]
            p2 = [1, yPos, 0]
            line = ansysPP.Line(name, p1, p2)
            
            lines.append(line)
            
        #Create a chart object to plot the data
        probedData = ansysPP.Chart('Chart' + str(dpIndex), 'X', 'Pressure')
        
        #Add series for lines
        for line in lines:
            probedData.addSeries(line.name, line)
            
        #Create an export object
        export = ansysPP.Export(probedData, self.rootDir + '\results_from_dp' + str(dpIndex) + '.csv')
            
        #Create session list and then the session object
        sessionList = []
        sessionList.extend(lines)
        sessionList.append(probedData)
        sessionList.append(export)
        session = ansysPP.SessionFile(sessionList)
        
        #Write the session file
        session.writeSessionFile(sessionFileName)