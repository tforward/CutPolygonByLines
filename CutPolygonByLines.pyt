
import os
import arcpy

# ================================================================================
# ArcPy Settings
# ================================================================================

arcpy.env.overwriteOutput = True
arcpy.SetLogHistory(False)

# ================================================================================

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Cut Polygon by Lines"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [Tool]

def defineParam(displayName, name, datatype, defaultValue=None,
    parameterType="Required", direction="Input", filterList=None, filterType=None):
    """
    This method pre-populates the parameterType
    and direction parameters and leaves the setting a default value for the
    newly created parameter as optional.

    https://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/defining-parameters-in-a-python-toolbox.htm
    https://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/defining-parameter-data-types-in-a-python-toolbox.htm

    Datatype can be a list of string values ex: ["one", "two", "three"] or just one string
    """
    param = arcpy.Parameter(
        displayName = displayName,
        name = name,
        datatype = datatype,
        parameterType = parameterType,
        direction = direction
    )

    if filterList is not None:
        param.filter.list = filterList
        if filterType is not None:
            param.filter.type = filterType

    param.value = defaultValue
    return param

class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Cut Polygon By Polylines"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        inputPolygon = defineParam(displayName="Input Polygon", name="inputPolygon", datatype="DEFeatureClass", filterList=["Polygon"])
        inputLines = defineParam(displayName="Input Lines", name="inputLines", datatype="DEFeatureClass", filterList=["Polyline"])
        outputPolygon = defineParam(displayName="Output Polygon Location", name="outputLocation", datatype="DEFeatureClass", direction="Output")

        params = [inputPolygon, inputLines, outputPolygon]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, param, messages):
        """Parameters"""
        inputPoly = param[0].valueAsText
        inputLine = param[1].valueAsText
        outputPoly = param[2].valueAsText

        # Need to update the tool so it outputs
        cut_geometry(inputPoly, inputLine, outputPoly)

        return

# ================================================================================
# Code
# ================================================================================

def cut_geometry(to_cut, cutter, outputPath):
    """
    Cut a feature by a line, splitting it into its separate geometries.
    :param to_cut: The feature to cut.
    :param cutter: The polylines to cut the feature by. Must extent passed polygon.
    :output: The feature where the split geometry is added.
    """

    path = os.path.dirname(outputPath)

    arcpy.CopyFeatures_management(to_cut, outputPath)

    arcpy.AddField_management(outputPath, "SOURCE_OID", "LONG")
    geometries = []
    polygon = None

    edit = arcpy.da.Editor(path)
    edit.startEditing(False, False)

    insert_cursor = arcpy.da.InsertCursor(outputPath, ["SHAPE@", "SOURCE_OID"])
    
    to_cut_fields = ["SHAPE@", "OID@", "SOURCE_OID"]

    with arcpy.da.SearchCursor(cutter, "SHAPE@") as lines:
        for line in lines:
            with arcpy.da.UpdateCursor(outputPath, to_cut_fields) as polygons:
                for polygon in polygons:
                    if line[0].disjoint(polygon[0]) == False:
                        if polygon[2] == None:
                            id = polygon[1]
                        # Remove previous geom if additional cuts are needed for intersecting lines
                        if len(geometries) > 1:
                            del geometries[0] 
                        geometries.append([polygon[0].cut(line[0]), id])
                        polygons.deleteRow()
                for geometryList in geometries:
                    for geometry in geometryList[0]:
                        if geometry.area > 0:
                            insert_cursor.insertRow([geometry, geometryList[1]])

    edit.stopEditing(True)