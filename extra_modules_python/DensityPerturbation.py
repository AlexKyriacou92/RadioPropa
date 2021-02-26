import radiopropa as RP
import numpy as np
from radiotools import helper as hp
#from ObserverPlane import ObserverPlane 


class PerturbationLayer(RP.Module):
    """
    A layer a radiopropa surface.
    Part of a candidate crossing the layer is reflected. 
    Future propagation in scalar field will take care of directivity change automatically???
    """
    def __init__(self, surface, thickness, threshold=0.01, fraction=0.023):
        RP.Module.__init__(self)
        self.__surface = surface
        self.__thickness = thickness 
        self.__threshold = threshold
        self.__fraction = fraction

    def process(self, candidate):
        if self.inLayer(candidate.current.getPosition()):
            normal = self.__surface.normal(candidate.current.getPosition())
            v = candidate.current.getDirection()
            cos_theta = v.dot(normal)
            
            if self.createdInLayer(candidate):
                u = normal * (cos_theta*v.getR())
                new_direction = (v - u) / (v-u).getR() #new direction parallel to layer
                candidate.current.setDirection(new_direction)

                #Propagation module bends the ray slightly downwards,
                #resulting in a straigt line with a small negative slope
                #with respect to the layer. Adjusting for the position 
                #overcomes this.
                self.positionCorrection(candidate, new_direction)

            elif self.inLayer(candidate.previous.getPosition()) and (abs(cos_theta) < self.__threshold):
                has_daugther_in_layer = False
                for secondary in candidate.secondaries:
                    has_daugther_in_layer = (has_daugther_in_layer or self.createdInLayer(secondary))

                if not has_daugther_in_layer:
                    #The secondary propagates further in layer because of very small fraction
                    secondary = candidate.clone(False)
                    secondary.created = candidate.current
                    E = candidate.current.getAmplitude()
                    secondary.current.setAmplitude(E*self.__fraction)
                    
                    u = normal * (cos_theta*v.getR())
                    new_direction = (v - u) / (v-u).getR() #new direction parallel to layer
                    secondary.current.setDirection(new_direction)

                    #Propagation module bends the ray slightly downwards,
                    #resulting in a straigt line with a small negative slope
                    #with respect to the layer. Adjusting for the position 
                    #overcomes this.
                    self.positionCorrection(secondary, new_direction)

                    secondary.limitNextStep(abs(abs(self.getDistance(secondary.current.getPosition()))-self.__thickness/2))
                    candidate.addSecondary(secondary)

        candidate.limitNextStep(abs(abs(self.getDistance(candidate.current.getPosition()))-self.__thickness/2))

    def positionCorrection(self, candidate, new_direction):
        p = candidate.previous.getPosition()
        c = candidate.current.getPosition()
        step_size = (c-p).getR()
        new_position = c + new_direction*step_size
        candidate.current.setPosition(new_position)

    def getCosTheta(self, position, direction):
        normal = self.__surface.normal(position)
        return direction.dot(normal)

    def getDistance(self, position):
        return self.__surface.distance(position)

    def getThickness(self):
        return self.__thickness

    def setThickness(self, new_thickness):
        self.__thickness = new_thickness

    def getThreshold(self):
        return self.__threshold

    def setThreshold(self, new_threshold):
        self.__threshold = new_threshold

    def parallelToLayer(self, position, direction):
        return (abs(self.getCosTheta()) < self.__threshold)

    def inLayer(self, position):
        distance = self.__surface.distance(position)
        return (abs(distance) <= self.__thickness/2)

    def createdInLayer(self,candidate):
        createdDistance = self.__surface.distance(candidate.created.getPosition())
        return (abs(createdDistance) <= self.__thickness/2)


class PerturbationHorizontal(PerturbationLayer):
    def __init__(self,z,thickness):
        layer_pos = RP.Vector3d(0,0,z)
        surface = RP.Plane(layer_pos, RP.Vector3d(0,0,1))
        PerturbationLayer.__init__(self, surface, thickness)

    def position_correction(self, candidate, direction):
        p = candidate.previous.getPosition()
        c = candidate.current.getPosition()
        new_position = RP.Vector3d(c.x,c.y,p.z)
        candidate.current.setPosition(new_position)